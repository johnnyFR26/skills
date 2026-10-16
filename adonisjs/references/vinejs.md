# VineJS (validação) — AdonisJS v6

## Índice
1. Uso básico · 2. Tipos de schema · 3. Regras de string/número/data · 4. Campos opcionais/condicionais · 5. Regras de banco (unique/exists) · 6. Arquivos · 7. Mensagens e erros · 8. Meta-dados · 9. Regras e tipos custom · 10. Inferência de tipos · 11. Padrões de CRUD

## 1. Uso básico
```bash
node ace make:validator post     # app/validators/post.ts
```
```ts
import vine from '@vinejs/vine'

export const createPostValidator = vine.compile(
  vine.object({
    title: vine.string().trim().minLength(3).maxLength(120),
    body: vine.string().trim(),
    tags: vine.array(vine.string().trim()).optional(),
  })
)
```
```ts
// controller
const payload = await request.validateUsing(createPostValidator)
// fora de HTTP
const data = await createPostValidator.validate(input)
```
- `validateUsing` valida corpo + query string + arquivos. **Params de rota não entram automaticamente**: passe via `meta` ou valide `{ ...request.all(), ...params }` conscientemente.
- Campos não declarados são **removidos** do resultado (ótimo contra mass assignment). Use `.allowUnknownProperties()` só se precisar.
- Falha → `E_VALIDATION_ERROR` (422). API/JSON recebe `{ errors: [{ message, rule, field, meta? }] }`; web volta com flash de erros.
- Validators são compilados: defina **no nível do módulo**, nunca dentro da função do controller.

## 2. Tipos de schema
| Schema | Observação |
|---|---|
| `vine.string()` | |
| `vine.number()` | aceita string numérica por padrão (`{ strict: true }` desativa) |
| `vine.boolean()` | converte `"true"/"1"/"on"` etc. (`{ strict: true }` desativa) |
| `vine.date()` | retorna `Date`; `{ formats: ['YYYY-MM-DD'] }` |
| `vine.enum(['a','b'])` / `vine.enum(MeuEnum)` | |
| `vine.array(schema)` | |
| `vine.object({...})` | |
| `vine.record(schema)` | objeto com chaves dinâmicas |
| `vine.tuple([a, b])` | |
| `vine.accepted()` | checkbox "aceito os termos" |
| `vine.literal('x')` / `vine.any()` | |
| `vine.file({ size, extnames })` | só com Adonis (upload) |
| `vine.unionOfTypes([...])`, `vine.union([...])`, `vine.group([...])` | condicionais |

## 3. Regras principais
**String:** `email()`, `url()`, `activeUrl()`, `uuid()`, `alpha()`, `alphaNumeric()`, `regex(/x/)`, `minLength/maxLength/fixedLength`, `confirmed()` (exige `<campo>_confirmation`), `sameAs('campo')`, `notSameAs`, `in([...])`, `notIn`, `startsWith`, `endsWith`, `mobile()`, `ipAddress()`, `creditCard()`, `hexCode()`, `ascii()`, `jwt()`, `trim()`, `escape()`, `normalizeEmail()`, `normalizeUrl()`, `toLowerCase()`, `toUpperCase()`, `camelCase()`, `snakeCase()`, `sanitizeHtml`.
**Number:** `min`, `max`, `range([1,10])`, `positive()`, `negative()`, `decimal([0,2])`, `withoutDecimals()`, `in([...])`, `notIn`.
**Date:** `after('today')`, `before('tomorrow')`, `afterOrEqual`, `beforeOrEqual`, `sameAs('campo')`, `afterField('start')`, `beforeField('end')`, `weekday()`, `weekend()`.
**Array:** `minLength`, `maxLength`, `fixedLength`, `notEmpty()`, `distinct()`, `compact()`.
**Qualquer:** `.transform((v) => ...)`, `.use(minhaRegra())`.

## 4. Opcionais e condicionais
```ts
vine.string().optional()      // pode faltar (undefined); null = erro
vine.string().nullable()      // pode ser null; faltar = erro
vine.string().optional().nullable()   // aceita ambos → use p/ PATCH/clear de campo

vine.object({
  type: vine.enum(['personal', 'company']),
  cnpj: vine.string().requiredWhen('type', '=', 'company'),
  phone: vine.string().optional().requiredIfMissing('email'),
  email: vine.string().email().optional().requiredIfMissing('phone'),
})
```
Variantes: `requiredWhen`, `requiredIfExists`, `requiredIfMissing`, `requiredIfAnyExist`, `requiredIfAllExist`, `requiredIfAnyMissing`, `requiredIfAllMissing`, `requiredUnless`.

Strings vazias de formulários: por padrão `""` vira `null` (config `convertEmptyStringsToNull`). Combine com `.optional()` / `.nullable()`.

Grupos condicionais (schemas diferentes por valor):
```ts
const schema = vine.object({ role: vine.enum(['user', 'admin']) })
  .merge(vine.group([
    vine.group.if((d) => d.role === 'admin', { permissions: vine.array(vine.string()) }),
    vine.group.else({}),
  ]))
```

## 5. Regras de banco (via Lucid)
```ts
vine.string().email().unique(async (db, value) => {
  const row = await db.from('users').where('email', value).first()
  return !row                    // true = válido
})
vine.number().exists(async (db, value) => !!(await db.from('categories').where('id', value).first()))
```
Update ignorando o próprio registro (use meta):
```ts
export const updateUserValidator = vine
  .withMetaData<{ userId: number }>()
  .compile(vine.object({
    email: vine.string().email().unique(async (db, value, field) => {
      const row = await db.from('users').where('email', value).whereNot('id', field.meta.userId).first()
      return !row
    }),
  }))
await request.validateUsing(updateUserValidator, { meta: { userId: params.id } })
```

## 6. Arquivos
```ts
vine.object({
  avatar: vine.file({ size: '2mb', extnames: ['jpg', 'png', 'webp'] }),
  docs: vine.array(vine.file({ size: '5mb', extnames: ['pdf'] })).maxLength(3).optional(),
})
// controller
const { avatar } = await request.validateUsing(v)
await avatar.move(app.makePath('storage/uploads'), { name: `${cuid()}.${avatar.extname}` })
// ou com Drive: await drive.use().putStream? (veja ecosystem.md)
```
Valide também o MIME real (`avatar.type`/`subtype`) quando segurança importar.

## 7. Mensagens e erros
```ts
import { SimpleMessagesProvider } from '@vinejs/vine'

createPostValidator.messagesProvider = new SimpleMessagesProvider(
  {
    required: 'O campo {{ field }} é obrigatório',
    'title.minLength': 'O título precisa de pelo menos {{ min }} caracteres',
    email: 'E-mail inválido',
    'email.unique': 'Este e-mail já está em uso',
  },
  { title: 'título', email: 'e-mail' }          // apelidos de campo
)
```
Global (pt-BR) em `start/` ou provider: `vine.messagesProvider = new SimpleMessagesProvider({...})`. Com `@adonisjs/i18n`, os validators usam `resources/lang/<locale>/validator.json` automaticamente.
Capturar manualmente:
```ts
import { errors } from '@vinejs/vine'
try { await validator.validate(data) } catch (e) { if (e instanceof errors.E_VALIDATION_ERROR) e.messages }
```
Arrays/objetos: `field` vem como `items.0.name`; use `*` em mensagens: `'items.*.name.required'`.

## 8. Meta-dados
Passa contexto (usuário logado, params, tenant) para as regras: `vine.withMetaData<{ ... }>()` + `{ meta }` na validação; acessível em `field.meta` dentro de regras e `unique/exists`.

## 9. Regras e tipos custom
```ts
import vine, { VineString } from '@vinejs/vine'
import type { FieldContext } from '@vinejs/vine/types'

const cpf = vine.createRule((value, _opts, field: FieldContext) => {
  if (typeof value !== 'string') return          // regra roda só se for string
  if (!isValidCpf(value)) field.report('O {{ field }} não é um CPF válido', 'cpf', field)
})

declare module '@vinejs/vine' {
  interface VineString { cpf(): this }
}
VineString.macro('cpf', function (this: VineString) { return this.use(cpf()) })
// uso: vine.string().cpf()
```
Coloque macros num arquivo carregado como preload (`start/validator.ts` e registre em `adonisrc.ts → preloads`).
Regra assíncrona: a função pode ser `async`. Se a regra transforma o valor, use `field.mutate(novo, field)`. Para pular regras seguintes em campo vazio: `vine.createRule(fn, { implicit: true })` só quando precisa rodar em campo ausente.

## 10. Inferência de tipos
```ts
import type { Infer } from '@vinejs/vine/types'
export type CreatePostDTO = Infer<typeof createPostValidator>
```

## 11. Padrões de CRUD
```ts
// create: tudo obrigatório
// update (PATCH): mesmos campos com .optional()
export const updatePostValidator = vine.compile(vine.object({
  title: vine.string().trim().minLength(3).optional(),
  body: vine.string().trim().optional(),
}))

// listagem com filtros (query string)
export const listPostsValidator = vine.compile(vine.object({
  page: vine.number().positive().optional(),
  limit: vine.number().range([1, 100]).optional(),
  q: vine.string().trim().optional(),
  sort: vine.enum(['createdAt', 'title']).optional(),
}))
const { page = 1, limit = 20, q } = await request.validateUsing(listPostsValidator)
```
Dicas: normalize e-mails (`normalizeEmail()`), faça `trim()` em strings de usuário, valide enums contra o TypeScript enum, e nunca confie em campos como `role`/`userId` vindos do cliente.
