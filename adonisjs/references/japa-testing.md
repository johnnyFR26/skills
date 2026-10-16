# Testes com Japa — AdonisJS v6

## Índice
1. Setup · 2. Suites e execução · 3. Anatomia do teste · 4. Assertions · 5. API client · 6. Banco de dados · 7. Autenticação nos testes · 8. Fakes (mail, events, drive, hash) · 9. Browser tests · 10. Padrões e dicas

## 1. Setup
Projetos criados pelo starter já vêm configurados. Para adicionar manualmente:
```bash
npm i -D @japa/runner @japa/assert @japa/plugin-adonisjs @japa/api-client
```
Plugins opcionais: `@japa/browser-client` (Playwright), `@japa/snapshot`, `@japa/file-system`, `@japa/openapi-assertions`.

`tests/bootstrap.ts` (essencial):
```ts
import { assert } from '@japa/assert'
import { apiClient } from '@japa/api-client'
import app from '@adonisjs/core/services/app'
import type { Config } from '@japa/runner/types'
import { pluginAdonisJS } from '@japa/plugin-adonisjs'
import testUtils from '@adonisjs/core/services/test_utils'
import { authApiClient } from '@adonisjs/auth/plugins/japa/api_client'
import { sessionApiClient } from '@adonisjs/session/plugins/api_client'

export const plugins: Config['plugins'] = [
  assert(), apiClient(), pluginAdonisJS(app), authApiClient(app), sessionApiClient(app),
]
export const runnerHooks: Required<Pick<Config, 'setup' | 'teardown'>> = {
  setup: [() => testUtils.db().migrate()],   // roda migrations antes da suíte
  teardown: [],
}
export const configureSuite: Config['configureSuite'] = (suite) => {
  if (['browser', 'functional', 'e2e'].includes(suite.name)) {
    return suite.setup(() => testUtils.httpServer().start())   // sobe o servidor HTTP
  }
}
```
`.env.test` (carregado quando `NODE_ENV=test`): use banco separado (ou sqlite `:memory:`), `SESSION_DRIVER=memory`, `LOG_LEVEL=silent`, `MAIL_MAILER` fake.

## 2. Suites e execução
`adonisrc.ts`:
```ts
tests: {
  suites: [
    { files: ['tests/unit/**/*.spec(.ts|.js)'], name: 'unit', timeout: 2000 },
    { files: ['tests/functional/**/*.spec(.ts|.js)'], name: 'functional', timeout: 30000 },
  ],
  forceExit: false,
}
```
```bash
node ace make:test posts --suite=functional
node ace test                         # tudo
node ace test unit                    # uma suíte
node ace test --files="posts"         # por arquivo
node ace test --tests="cria post"     # por título
node ace test --groups="Posts"        # por grupo
node ace test --tags="@slow"          # por tag
node ace test --watch                 # re-executa ao salvar
node ace test --bail --retries=2 --timeout=10000 --reporters=spec
```

## 3. Anatomia do teste
```ts
import { test } from '@japa/runner'

test.group('PostsController', (group) => {
  group.setup(async () => {})                 // 1x antes do grupo
  group.teardown(async () => {})
  group.each.setup(async () => {})            // antes de cada teste (pode retornar cleanup fn)
  group.each.teardown(async () => {})

  test('lista posts', async ({ assert, client }) => { /* ... */ })

  test('pula este').skip(true, 'motivo')      // skip condicional
  test('só este').pin()                       // roda apenas pinados
  test('lento').tags(['@slow']).timeout(10000)
  test('flaky').retry(3)
  test('espera falhar').fails()
  test('deve lançar').throws('mensagem')
  test('multiplos casos').with([{ a: 1, b: 2 }, { a: 2, b: 4 }])  // dataset: segundo arg é o item
})

test('dataset', async ({ assert }, { a, b }) => { assert.equal(b, a * 2) }).with([{ a: 1, b: 2 }])
test('cleanup', async ({ cleanup }) => { cleanup(() => console.log('limpou')) })
```
Contexto do teste: `assert`, `client`, `cleanup`, `route` (quando disponível), `visit`/`browserContext` (browser), `expect` (com `@japa/expect`).

## 4. Assertions (Chai `assert`)
```ts
assert.equal(a, b); assert.notEqual(a, b)
assert.deepEqual(obj1, obj2)
assert.isTrue(x); assert.isFalse(x); assert.isNull(x); assert.exists(x); assert.isUndefined(x)
assert.lengthOf(arr, 3); assert.isEmpty(arr)
assert.include(str, 'x'); assert.match(str, /regex/)
assert.properties(obj, ['id', 'title'])
assert.containsSubset(arr, [{ id: 1 }])
assert.isAbove(5, 3)
await assert.rejects(() => service.fail(), 'mensagem esperada')
assert.closeTo(0.3, 0.1 + 0.2, 0.0001)
```

## 5. API client
```ts
import router from '@adonisjs/core/services/router'

test('cria post', async ({ client }) => {
  const response = await client
    .post('/api/v1/posts')
    .json({ title: 'Oi', body: 'texto' })
    .header('Accept-Language', 'pt-BR')
    .qs({ draft: true })

  response.assertStatus(201)
  response.assertBodyContains({ title: 'Oi' })
})
```
Construtores: `.get/.post/.put/.patch/.delete`, `.json(obj)`, `.form(obj)`, `.field('k','v')`, `.file('avatar', path)`, `.header`, `.headers`, `.cookie`, `.qs`, `.withCsrfToken()`, `.redirects(0)`, `.timeout(ms)`.
Helpers de URL: `router.makeUrl('posts.show', { id: 1 })` (nome da rota) em vez de string solta.

Asserções de resposta: `assertStatus`, `assertBody(obj)` (igualdade exata), `assertBodyContains` (subconjunto, aceita arrays aninhados), `assertBodySubset`, `assertHeader('content-type', ...)`, `assertTextIncludes('...')`, `assertCookie`, `assertRedirectsTo('/login')`. Leitura: `response.status()`, `response.body()`, `response.headers()`, `response.text()`, `response.cookies()`. Depuração: `response.dumpBody()`, `response.dumpError()`, `response.dump()`.
Erros de validação (422): `response.assertStatus(422); response.assertBodyContains({ errors: [{ field: 'title', rule: 'required' }] })`.
Sessão/flash (com `sessionApiClient`): `.withSession({ k: 'v' })`, `response.assertSession('k', 'v')`, `response.assertFlashMessage('success', '...')`.

## 6. Banco de dados
```ts
import testUtils from '@adonisjs/core/services/test_utils'

group.each.setup(() => testUtils.db().withGlobalTransaction())   // ✅ padrão: rollback após cada teste
// alternativas
group.each.setup(() => testUtils.db().truncate())                // limpa tabelas (mais lento)
group.setup(() => testUtils.db().seed())
```
`withGlobalTransaction` só funciona se todo o código usa a conexão padrão (não crie transações paralelas conflitantes). Crie dados com Factories: `const user = await UserFactory.create()`.
Em sqlite `:memory:` os testes ficam rápidos; para features específicas do Postgres use um banco real de teste.

## 7. Autenticação nos testes
```ts
const user = await UserFactory.create()
// sessão
await client.get('/dashboard').loginAs(user)
// guard específico
await client.get('/api/me').withGuard('api').loginAs(user)
// token de acesso (guard access_tokens): loginAs gera token automaticamente
// com permissões/abilities: use tokens reais quando testar abilities
const token = await User.accessTokens.create(user)
await client.get('/api/me').bearerToken(token.value!.release())
```
(`loginAs` requer o plugin `authApiClient`.)

## 8. Fakes
```ts
import mail from '@adonisjs/mail/services/main'
import emitter from '@adonisjs/core/services/emitter'
import drive from '@adonisjs/drive/services/main'
import hash from '@adonisjs/core/services/hash'

// E-mail
const { mails } = mail.fake()
await client.post('/register').json({...})
mails.assertSent(WelcomeNotification, ({ message }) => message.hasTo('a@b.c'))
mails.assertNotSent(OtherMail)
mails.assertSentCount(1)
mail.restore()

// Eventos
const events = emitter.fake()
events.assertEmitted('user:registered')
events.assertNotEmitted('user:deleted')
emitter.restore()

// Drive (arquivos)
const fakeDisk = drive.fake()
await client.post('/avatar').file('avatar', './fixtures/a.png')
fakeDisk.assertExists('avatars/a.png')
drive.restore()

// Hash rápido nos testes
hash.fake(); /* ... */ hash.restore()
```
Sempre `restore()` em `group.each.teardown` ou use `cleanup(() => mail.restore())`.
Para dependências próprias, use o container: `app.container.swap(PaymentGateway, () => new FakeGateway())` e `app.container.restore(PaymentGateway)`.

## 9. Browser tests (Playwright)
```bash
node ace add @japa/browser-client   # e: npx playwright install
```
```ts
test('login', async ({ visit, browserContext }) => {
  const page = await visit('/login')
  await page.locator('input[name=email]').fill('a@b.c')
  await page.locator('input[name=password]').fill('secret')
  await page.getByRole('button', { name: 'Entrar' }).click()
  await page.assertPath('/dashboard')
  await page.assertTextContains('body', 'Bem-vindo')
})
// já autenticado (plugin authBrowserClient + sessionBrowserClient):
await browserContext.loginAs(user)
```
Rode em suíte separada (`browser`) com timeout maior, e use `testUtils.httpServer().start()` no `configureSuite`.

## 10. Padrões e dicas
- **Unit**: services/regras sem HTTP; **Functional**: rotas ponta a ponta com `client`; **Browser**: fluxos críticos de UI.
- Teste o contrato: status, corpo, efeitos colaterais (registro no banco, e-mail enviado, evento emitido).
- Uma asserção por comportamento; nomes de teste descrevem o comportamento ("retorna 403 se não for dono").
- Cubra: caminho feliz, validação (422), não autenticado (401), sem permissão (403), não encontrado (404).
- Nunca dependa de ordem entre testes; cada teste cria seus dados.
- CI: `NODE_ENV=test node ace test` com banco de serviço; rode `node ace migration:run` antes ou use o hook `migrate()`.
