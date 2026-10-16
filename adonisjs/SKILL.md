---
name: adonisjs
description: Guia para desenvolver aplicações com AdonisJS v6 (TypeScript, ESM) — rotas, controllers, Lucid ORM, migrations, VineJS, autenticação, middleware, Edge, testes com Japa e comandos Ace. Use SEMPRE que o usuário mencionar AdonisJS, Adonis, Lucid, VineJS, Edge, Ace (node ace), Japa, start/routes.ts, ou pedir backend Node com esse framework, mesmo sem citar o nome. Evita código da v5 (@ioc:Adonis/...).
---

# AdonisJS v6

Framework Node.js full-stack, TypeScript-first, ESM, com injeção de dependência. Antes de escrever código, **confirme a versão** (`package.json` → `@adonisjs/core`). Esta skill cobre a **v6**. Se for v5, avise o usuário: a sintaxe é diferente.

## Regras que evitam erros comuns

1. **Nunca use imports da v5** (`@ioc:Adonis/Core/Route`, `@ioc:Adonis/Lucid/Orm`). Na v6 use imports reais e *subpath imports* do `package.json`:
   - `#controllers/*`, `#models/*`, `#validators/*`, `#services/*`, `#middleware/*`, `#start/*`, `#config/*`, `#exceptions/*`
2. **ESM**: imports locais de arquivos relativos precisam de extensão `.js`; com aliases `#...` não precisa.
3. **Sempre gere arquivos com Ace** (`node ace make:*`) em vez de criar do zero — garante nomes e local corretos.
4. **Nomes de arquivo em snake_case**: `posts_controller.ts`, `post.ts` (model, singular), `create_post_validator.ts`.
5. **Instale pacotes oficiais com `node ace add <pacote>`** (instala + configura). Não use só `npm i`.
6. Controllers em rotas são **lazy-loaded**.
7. Variáveis de ambiente: declare/valide em `start/env.ts` e acesse com `import env from '#start/env'`. Nunca `process.env` direto na aplicação.

## Criar projeto

```bash
npm init adonisjs@latest meu-app -- --kit=api   # web | api | hypermedia | inertia | slim
cd meu-app
node ace serve --hmr
```

Kit `api` → JSON + auth por token. Kit `web` → Edge + sessão. `inertia` → React/Vue/Svelte.

## Estrutura

```
app/controllers  app/models  app/validators  app/middleware  app/services  app/exceptions
config/          database/migrations  database/seeders  database/factories
start/routes.ts  start/kernel.ts  start/env.ts
resources/views (Edge)   tests/
bin/server.ts    adonisrc.ts
```

## Comandos Ace essenciais

```bash
node ace make:controller posts            # PostsController
node ace make:controller posts -r         # com métodos de resource
node ace make:model Post -m -c            # model + migration + controller
node ace make:migration add_slug_to_posts --alter
node ace make:validator post
node ace make:middleware silent_auth
node ace make:service post_service
node ace make:seeder user
node ace make:factory Post
node ace make:test posts --suite=functional
node ace make:exception
node ace list:routes
node ace migration:run | migration:rollback | migration:fresh --seed | migration:status
node ace db:seed
node ace test            # Japa
node ace build
```

## Rotas (`start/routes.ts`)

```ts
import router from '@adonisjs/core/services/router'
import { middleware } from '#start/kernel'

const PostsController = () => import('#controllers/posts_controller')

router.get('/', async () => ({ hello: 'world' }))

router
  .group(() => {
    router.resource('posts', PostsController).apiOnly()
    router.get('me', [() => import('#controllers/profile_controller'), 'show'])
  })
  .prefix('/api/v1')
  .use(middleware.auth())
```

## Controller

```ts
import type { HttpContext } from '@adonisjs/core/http'
import Post from '#models/post'
import { createPostValidator } from '#validators/post'

export default class PostsController {
  async index({ request }: HttpContext) {
    const page = request.input('page', 1)
    return Post.query().preload('author').orderBy('createdAt', 'desc').paginate(page, 20)
  }

  async store({ request, auth }: HttpContext) {
    const payload = await request.validateUsing(createPostValidator)
    return Post.create({ ...payload, userId: auth.user!.id })
  }

  async show({ params }: HttpContext) {
    return Post.findOrFail(params.id)
  }

  async destroy({ params, response }: HttpContext) {
    const post = await Post.findOrFail(params.id)
    await post.delete()
    return response.noContent()
  }
}
```

`findOrFail` lança exceção que o Adonis converte em 404 automaticamente.

## Validação (VineJS)

```ts
// app/validators/post.ts
import vine from '@vinejs/vine'

export const createPostValidator = vine.compile(
  vine.object({
    title: vine.string().trim().minLength(3).maxLength(120),
    body: vine.string().trim(),
    email: vine.string().email().unique(async (db, value) => {
      return !(await db.from('users').where('email', value).first())
    }),
  })
)
```

Falhas de validação retornam 422 automaticamente.

## Lucid ORM

```ts
import { DateTime } from 'luxon'
import { BaseModel, column, belongsTo, hasMany } from '@adonisjs/lucid/orm'
import type { BelongsTo, HasMany } from '@adonisjs/lucid/types/relations'
import User from '#models/user'
import Comment from '#models/comment'

export default class Post extends BaseModel {
  @column({ isPrimary: true })
  declare id: number

  @column()
  declare title: string

  @column()
  declare userId: number

  @belongsTo(() => User)
  declare author: BelongsTo<typeof User>

  @hasMany(() => Comment)
  declare comments: HasMany<typeof Comment>

  @column.dateTime({ autoCreate: true })
  declare createdAt: DateTime

  @column.dateTime({ autoCreate: true, autoUpdate: true })
  declare updatedAt: DateTime | null
}
```

- Use `declare` nas propriedades (não inicialize).
- Colunas no model em camelCase; no banco, snake_case (a naming strategy converte).
- Esconder campo na serialização: `@column({ serializeAs: null })`.
- Transações: `import db from '@adonisjs/lucid/services/db'` → `db.transaction(async (trx) => {...})`.

## Migration

```ts
import { BaseSchema } from '@adonisjs/lucid/schema'

export default class extends BaseSchema {
  protected tableName = 'posts'

  async up() {
    this.schema.createTable(this.tableName, (table) => {
      table.increments('id')
      table.integer('user_id').unsigned().references('users.id').onDelete('CASCADE')
      table.string('title').notNullable()
      table.timestamp('created_at')
      table.timestamp('updated_at')
    })
  }

  async down() {
    this.schema.dropTable(this.tableName)
  }
}
```

Nunca edite uma migration já executada em produção; crie uma nova com `--alter`.

## Autenticação

```bash
node ace add @adonisjs/auth --guard=session      # web
node ace add @adonisjs/auth --guard=access_tokens # API
```

- Model `User` usa `compose(BaseModel, AuthFinder)` com `withAuthFinder` (hash de senha automático).
- Login: `const user = await User.verifyCredentials(email, password); await auth.use('web').login(user)`.
- Tokens: `User.accessTokens.create(user)` → devolver `token.value!.release()`.
- Proteger rotas: `.use(middleware.auth())`; usuário em `auth.user`.
- Autorização: Bouncer (`node ace add @adonisjs/bouncer`).

## Injeção de dependência

```ts
import { inject } from '@adonisjs/core'
import PostService from '#services/post_service'

@inject()
export default class PostsController {
  constructor(protected posts: PostService) {}
}
```

Para métodos de controller, o `HttpContext` continua como primeiro parâmetro; services extras vêm depois com `@inject()` no método.

## Middleware

Registre em `start/kernel.ts`: `server.use` (global), `router.use` (rotas), `router.named({...})` (nomeado, usado via `middleware.nome()`).

## Edge (web)

```edge
@layout()
  <h1>{{ post.title }}</h1>
  @each(comment in post.comments)
    <p>{{ comment.body }}</p>
  @end
@end
```

No controller: `return view.render('pages/post', { post })`.

## Testes (Japa)

```ts
import { test } from '@japa/runner'
import testUtils from '@adonisjs/core/services/test_utils'

test.group('Posts', (group) => {
  group.each.setup(() => testUtils.db().withGlobalTransaction())

  test('lista posts', async ({ client }) => {
    const response = await client.get('/api/v1/posts')
    response.assertStatus(200)
  })
})
```

Rodar: `node ace test` ou `node ace test functional --files=posts`.

## Boas práticas

- Controllers finos; regra de negócio em `app/services`.
- Sempre validar entrada com VineJS; nunca usar `request.all()` direto em `create`.
- Evitar N+1: `preload` para relações.
- Variáveis sensíveis só em `.env` (nunca commitar); gere `APP_KEY` com `node ace generate:key`.
- Em produção: `node ace build`, depois `node ace migration:run --force` e `node bin/server.js` dentro de `build/`.

## Quando precisar de detalhes

Leia `references/recipes.md` para: upload de arquivos, jobs/eventos, e-mail, CORS, rate limit, tratamento de erros e deploy. Em caso de dúvida sobre API específica, consulte https://docs.adonisjs.com.
