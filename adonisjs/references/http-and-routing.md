# HTTP, rotas, middleware, erros e views — AdonisJS v6

## Índice
1. Rotas · 2. HttpContext (request/response) · 3. Middleware · 4. Tratamento de erros · 5. Edge · 6. Inertia · 7. Env e config · 8. Container e providers

## 1. Rotas
```ts
router.get('/posts/:id', [PostsController, 'show']).as('posts.show').where('id', router.matchers.number())
router.post('/posts', [PostsController, 'store'])
router.on('/about').render('pages/about')           // rota que só renderiza view
router.get('/old', ({ response }) => response.redirect().toRoute('posts.index'))

router.resource('posts', PostsController)           // index create store show edit update destroy
router.resource('posts', PostsController).apiOnly() // sem create/edit
router.resource('posts', PostsController).only(['index', 'show'])
router.resource('users.posts', UserPostsController) // aninhado: /users/:user_id/posts

router.group(() => { /* ... */ }).prefix('/admin').as('admin').domain('admin.exemplo.com').use(middleware.auth())
router.shallowResource('users.posts', ...)           // rotas filhas rasas
```
- Nome de rota gera URL: `router.makeUrl('posts.show', { id: 1 })`; Edge: `{{ route('posts.show', { id: 1 }) }}`; redirect: `response.redirect().toRoute('posts.show', { id })`.
- URLs assinadas: `router.makeSignedUrl('unsubscribe', { id }, { expiresIn: '30m' })` + `request.hasValidSignature()`.
- Matchers: `number()`, `uuid()`, `slug()`; wildcard `/files/*`.
- Listar: `node ace list:routes`.
- Sempre importe controllers com **lazy import**: `const X = () => import('#controllers/x_controller')`.

## 2. HttpContext
```ts
async handle({ request, response, params, auth, session, view, logger, bouncer, i18n }: HttpContext) {}
```
**Request:** `request.all()`, `.input('k', default)`, `.only([...])`, `.except([...])`, `.qs()`, `.param('id')` / `params`, `.header('x')`, `.cookie('k')`, `.ip()`, `.url()`, `.method()`, `.accepts(['json'])`, `.file('f')`, `.files('f')`, `.body()`, `request.id()`.
**Response:** `return obj` (JSON automático) · `response.status(201).send(...)` · `response.created(x)` · `response.noContent()` · `response.notFound()` · `response.badRequest()` · `response.unauthorized()` · `response.forbidden()` · `response.redirect('/x')` · `.back()` · `.toRoute('name', params)` · `response.header('k','v')` · `.cookie('k','v', opts)` · `response.download(path)` · `response.attachment(path, 'nome.pdf')` · `response.stream(readable)` · `response.abort({ message }, 403)`.
- Retornar string = HTML/text; objeto/array/model/paginator = JSON.
- Body parser: `config/bodyparser.ts` (limites JSON/multipart, tipos aceitos).
- Contexto em serviços sem parâmetro: `import { HttpContext } from '@adonisjs/core/http'; HttpContext.getOrFail()` (requer `useAsyncLocalStorage: true` em `config/app.ts`).

## 3. Middleware
```bash
node ace make:middleware log_request
```
```ts
import type { HttpContext } from '@adonisjs/core/http'
import type { NextFn } from '@adonisjs/core/types/http'

export default class LogRequestMiddleware {
  async handle(ctx: HttpContext, next: NextFn, options?: { level: string }) {
    const start = Date.now()
    const output = await next()                      // tudo após = pós-processamento
    ctx.logger.info({ ms: Date.now() - start }, 'request')
    return output
  }
}
```
`start/kernel.ts`:
```ts
server.use([...])                  // global (roda também em 404)
router.use([...])                  // global p/ rotas existentes
export const middleware = router.named({
  auth: () => import('#middleware/auth_middleware'),
  log: () => import('#middleware/log_request_middleware'),
})
// uso: .use(middleware.log({ level: 'debug' }))
```
Ordem importa. Container middleware (`ContainerBindings`) injeta dependências via `@inject()` no constructor.

## 4. Tratamento de erros
`app/exceptions/handler.ts`:
```ts
export default class HttpExceptionHandler extends ExceptionHandler {
  protected debug = !app.inProduction
  async handle(error: unknown, ctx: HttpContext) {
    if (error instanceof errors.E_ROW_NOT_FOUND) return ctx.response.status(404).send({ message: 'Recurso não encontrado' })
    return super.handle(error, ctx)
  }
  async report(error: unknown, ctx: HttpContext) { return super.report(error, ctx) }  // envie p/ Sentry etc.
}
```
Exception própria:
```ts
// node ace make:exception PaymentFailed
import { Exception } from '@adonisjs/core/exceptions'
export default class PaymentFailedException extends Exception {
  static status = 402
  static code = 'E_PAYMENT_FAILED'
}
throw new PaymentFailedException('Cartão recusado')
```
Erros comuns: `E_ROW_NOT_FOUND` (404 de `findOrFail`), `E_VALIDATION_ERROR` (422), `E_ROUTE_NOT_FOUND` (404), `E_UNAUTHORIZED_ACCESS` (401), `E_AUTHORIZATION_FAILURE` (403), `E_INVALID_CREDENTIALS` (400).
Páginas de status em Edge: `statusPages` no handler (`{ '404': 'errors/not_found', '500..599': 'errors/server_error' }`).
Nunca exponha stack em produção (`debug` false).

## 5. Edge (templates)
```edge
{{-- resources/views/pages/posts/index.edge --}}
@layout.app({ title: 'Posts' })
  @each(post in posts)
    @component('components/card', { title: post.title })
      <p>{{ post.excerpt }}</p>
      <a href="{{ route('posts.show', { id: post.id }) }}">Ler</a>
    @end
  @else
    <p>Nenhum post.</p>
  @end

  <form method="POST" action="{{ route('posts.store') }}">
    {{ csrfField() }}
    <input name="title" value="{{ flashMessages.get('title') || '' }}">
    @inputError('title') <span>{{ $message }}</span> @end
  </form>
@end
```
- `{{ }}` escapa HTML; `{{{ html }}}` não escapa (só conteúdo confiável).
- Diretivas: `@if/@elseif/@else`, `@each`, `@include`, `@component/@!component`, `@layout`, `@eval`, `@let`, `@can`, `@vite(['resources/js/app.js'])`, `@assetsPath`.
- Controller: `return view.render('pages/posts/index', { posts })`.
- Globais/helpers em `start/view.ts` (`edge.global('appName', 'X')`).

## 6. Inertia
```bash
node ace add @adonisjs/inertia   # escolhe React/Vue/Svelte/Solid + SSR opcional
```
```ts
return inertia.render('posts/index', { posts: PostDto.fromArray(posts) })
```
- Props compartilhadas em `config/inertia.ts` (`sharedData`).
- Props preguiçosas: `inertia.always()`, `inertia.optional()`, `inertia.defer()`.
- Erros de validação e flash chegam como `errors` / props compartilhadas.
- Use DTOs (não o model direto) para controlar o que vai ao front.

## 7. Env e config
`start/env.ts`:
```ts
import { Env } from '@adonisjs/core/env'
export default await Env.create(new URL('../', import.meta.url), {
  NODE_ENV: Env.schema.enum(['development', 'production', 'test'] as const),
  PORT: Env.schema.number(),
  APP_KEY: Env.schema.string(),
  DB_HOST: Env.schema.string({ format: 'host' }),
  REDIS_URL: Env.schema.string.optional(),
})
```
Uso: `import env from '#start/env'` → `env.get('PORT')` (tipado). Arquivos: `.env`, `.env.test`, `.env.production`. Nunca commite `.env`; mantenha `.env.example`.
Config própria: crie `config/x.ts` com `defineConfig`/objeto e leia com `import config from '@adonisjs/core/services/config'; config.get('x.key')`.

## 8. Container e providers
```ts
import { inject } from '@adonisjs/core'
@inject()
export default class OrderService {
  constructor(protected mailer: MailService, protected logger: Logger) {}
}
// controller: @inject() no método ou na classe; o container resolve construtores recursivamente
import app from '@adonisjs/core/services/app'
const svc = await app.container.make(OrderService)
```
Bindings/singletons em provider:
```bash
node ace make:provider payment
```
```ts
export default class PaymentProvider {
  constructor(protected app: ApplicationService) {}
  register() { this.app.container.singleton(PaymentGateway, async () => new StripeGateway(env.get('STRIPE_KEY'))) }
  async boot() {}      // outros bindings já disponíveis
  async start() {}     // app pronta p/ iniciar
  async ready() {}     // servidor HTTP no ar
  async shutdown() {}  // limpeza
}
```
Registre em `adonisrc.ts → providers`. Use `{ file, environment: ['web'] }` para limitar a ambientes (`web`, `console`, `test`, `repl`).
Troca em testes: `app.container.swap(PaymentGateway, () => fake)`.
