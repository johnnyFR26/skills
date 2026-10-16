# Autenticação e autorização — AdonisJS v6

## Índice
1. Instalação e guards · 2. Model User · 3. Sessão (web) · 4. Access tokens (API) · 5. Middleware e acesso ao usuário · 6. Registro/login/logout · 7. Social login (Ally) · 8. Bouncer (autorização) · 9. Segurança

## 1. Instalação e guards
```bash
node ace add @adonisjs/auth --guard=session         # apps web (cookie)
node ace add @adonisjs/auth --guard=access_tokens   # APIs (bearer opaco)
node ace add @adonisjs/auth --guard=basic_auth      # HTTP Basic
```
Config em `config/auth.ts` (`default` guard + `guards`). Cria `app/middleware/auth_middleware.ts`, `guest_middleware.ts`, `silent_auth_middleware.ts` e migration `auth_access_tokens` (tokens).
Para sessão: `@adonisjs/session` também é necessário (instalado junto no kit web).

## 2. Model User
```ts
import { compose } from '@adonisjs/core/helpers'
import hash from '@adonisjs/core/services/hash'
import { withAuthFinder } from '@adonisjs/auth/mixins/lucid'
import { DbAccessTokensProvider } from '@adonisjs/auth/access_tokens'
import { BaseModel, column } from '@adonisjs/lucid/orm'

const AuthFinder = withAuthFinder(() => hash.use('scrypt'), {
  uids: ['email'],
  passwordColumnName: 'password',
})

export default class User extends compose(BaseModel, AuthFinder) {
  @column({ isPrimary: true }) declare id: number
  @column() declare email: string
  @column({ serializeAs: null }) declare password: string

  static accessTokens = DbAccessTokensProvider.forModel(User, {
    expiresIn: '30 days',
    prefix: 'oat_',
    table: 'auth_access_tokens',
    type: 'auth_token',
    tokenSecretLength: 40,
  })
}
```
O mixin faz **hash automático da senha** ao salvar. Não faça hash manual de novo (duplo hash).

## 3. Sessão (web)
```ts
const user = await User.verifyCredentials(email, password)  // lança E_INVALID_CREDENTIALS (mensagem genérica)
await auth.use('web').login(user, !!rememberMe)
await auth.use('web').logout()
```
- Flash de erro de login: `session.flash('error', 'Credenciais inválidas')`.
- Rotas: `.use(middleware.auth())` para logados; `.use(middleware.guest())` para login/registro.
- Proteção CSRF: `@adonisjs/shield` (`{{ csrfField() }}` em forms Edge).

## 4. Access tokens (API)
```ts
// login
const user = await User.verifyCredentials(email, password)
const token = await User.accessTokens.create(user, ['*'], { name: 'mobile', expiresIn: '7 days' })
return { type: 'bearer', token: token.value!.release(), expiresAt: token.expiresAt }
// logout
const user = auth.getUserOrFail()
await User.accessTokens.delete(user, user.currentAccessToken.identifier)
```
- O valor do token só pode ser lido **uma vez** na criação (`release()`); o banco guarda hash.
- Abilities: `create(user, ['posts:read', 'posts:write'])` e checagem `user.currentAccessToken.allows('posts:write')` (ou via Bouncer).
- Cliente envia `Authorization: Bearer oat_...`.
- Listar/revogar: `User.accessTokens.all(user)`, `.delete(user, id)`.

## 5. Middleware e acesso ao usuário
```ts
router.group(() => {...}).use(middleware.auth({ guards: ['api'] }))      // exige login
router.get('/home', ...).use(middleware.silentAuth())                    // identifica sem exigir
```
No controller (`HttpContext`):
```ts
auth.user                 // User | undefined
auth.getUserOrFail()      // lança se não logado
await auth.check()        // boolean (sem lançar)
await auth.authenticate() // lança E_UNAUTHORIZED_ACCESS
auth.isAuthenticated
auth.use('api').user      // guard específico
```
Edge: `@if(auth.isAuthenticated) ... @end` (com `silentAuth` na rota).
Redirecionamento de não autenticados em `app/middleware/auth_middleware.ts` (`redirectTo = '/login'`; em APIs responde 401 JSON).

## 6. Registro / login / logout (esqueleto API)
```ts
// validators/auth.ts
export const registerValidator = vine.compile(vine.object({
  fullName: vine.string().trim().maxLength(100).optional(),
  email: vine.string().email().normalizeEmail().unique(async (db, v) => !(await db.from('users').where('email', v).first())),
  password: vine.string().minLength(8).confirmed(),
}))
export const loginValidator = vine.compile(vine.object({
  email: vine.string().email().normalizeEmail(),
  password: vine.string(),
}))

// controller
async register({ request }: HttpContext) {
  const data = await request.validateUsing(registerValidator)
  const user = await User.create(data)           // password é hasheado pelo mixin
  const token = await User.accessTokens.create(user)
  return { user, token: token.value!.release() }
}
```
Recuperação de senha: gere token aleatório (`stringHelpers.random(64)`), guarde **hash** + expiração, envie e-mail por `@adonisjs/mail`, valide e invalide após uso. Verificação de e-mail: URL assinada (`router.makeSignedUrl('verify.email', { id }, { expiresIn: '1h' })` e `request.hasValidSignature()`).

## 7. Social login (Ally)
```bash
node ace add @adonisjs/ally     # github, google, discord, facebook, linkedin, twitter, spotify
```
```ts
router.get('/auth/:provider/redirect', ({ ally, params }) => ally.use(params.provider).redirect())
router.get('/auth/:provider/callback', async ({ ally, params, auth, response }) => {
  const social = ally.use(params.provider)
  if (social.accessDenied() || social.stateMisMatch() || social.hasError()) return response.unauthorized()
  const s = await social.user()
  const user = await User.firstOrCreate({ email: s.email! }, { fullName: s.name, password: stringHelpers.random(32) })
  await auth.use('web').login(user)
  return response.redirect('/')
})
```

## 8. Bouncer (autorização)
```bash
node ace add @adonisjs/bouncer
node ace make:policy post          # app/policies/post_policy.ts
```
Abilities (regras soltas, `app/abilities/main.ts`):
```ts
import { Bouncer } from '@adonisjs/bouncer'
export const isAdmin = Bouncer.ability((user: User) => user.role === 'admin')
```
Policies (por recurso):
```ts
import { BasePolicy } from '@adonisjs/bouncer'
import type { AuthorizerResponse } from '@adonisjs/bouncer/types'

export default class PostPolicy extends BasePolicy {
  viewAny(): AuthorizerResponse { return true }
  edit(user: User, post: Post): AuthorizerResponse { return user.id === post.userId }
  delete(user: User, post: Post): AuthorizerResponse { return user.id === post.userId || user.role === 'admin' }
}
```
Uso:
```ts
import PostPolicy from '#policies/post_policy'
import { isAdmin } from '#abilities/main'

await bouncer.with(PostPolicy).authorize('edit', post)   // lança E_AUTHORIZATION_FAILURE → 403
if (await bouncer.with(PostPolicy).allows('delete', post)) {...}
if (await bouncer.denies(isAdmin)) {...}
// usuário convidado (não logado): marque o método com @allowGuest()
```
Edge: `@can('edit', post)` / `@cannot(...)` com abilities; para policies use `@can('PostPolicy.edit', post)` (conforme registro em `app/policies/main.ts`).
Respostas customizadas: `return AuthorizationResponse.deny('Mensagem', 404)`.
Use `.use(middleware.initializeBouncer())` (já no kernel após instalar).

## 9. Segurança
- Mensagem de erro de login **genérica**; nunca revele se o e-mail existe.
- Limite tentativas com `@adonisjs/limiter` (`usingKey(`${ip}_${email}`)`).
- Cookies de sessão: `httpOnly`, `secure` em produção, `sameSite: 'lax'`.
- `APP_KEY` forte e secreta (`node ace generate:key`); rotacionar invalida sessões/cookies assinados.
- Escopos: valide propriedade do recurso (Bouncer) em **todo** endpoint com `:id`, não só na UI.
- Nunca retorne `password`/tokens em respostas (`serializeAs: null`).
