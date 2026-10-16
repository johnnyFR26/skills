---
name: adonisjs
description: Guia completo para desenvolver com AdonisJS v6 (TypeScript, ESM) — rotas, controllers, middleware, Lucid ORM (models, relações, migrations, factories), VineJS (validação), Japa (testes unitários, API e browser), Transmit (tempo real via SSE), autenticação (sessão e access tokens), Bouncer, Edge, Inertia, Drive, Mail, Limiter, Redis, Cache, eventos, comandos Ace e deploy. Use SEMPRE que o usuário mencionar AdonisJS/Adonis, Lucid, VineJS, Japa, Transmit, Edge, Bouncer, "node ace", start/routes.ts, ou pedir backend Node full-stack com esse framework, mesmo sem citar o nome. Evita código da v5 (@ioc:Adonis/...).
---

# AdonisJS v6 — guia principal

Framework Node.js full-stack, TypeScript-first, ESM, com container de injeção de dependência. Este arquivo traz as regras essenciais e **aponta para referências detalhadas**: leia só a que a tarefa exigir.

## Mapa de referências (leia sob demanda)

| Tarefa | Arquivo |
|---|---|
| Models, queries, relações, hooks, transações, migrations, seeders, factories | `references/lucid.md` |
| Validação de entrada, regras, mensagens, regras custom, unique/exists | `references/vinejs.md` |
| Testes: unit, functional (API), browser, fakes, DB em testes | `references/japa-testing.md` |
| Tempo real: canais, autorização, broadcast, cliente, Redis | `references/transmit.md` |
| Login, tokens, middleware auth, Ally, Bouncer (policies/abilities) | `references/auth-bouncer.md` |
| Rotas, request/response, middleware, erros, Edge, Inertia, env, providers/IoC | `references/http-and-routing.md` |
| Session, Shield, CORS, Drive, Mail, Limiter, Redis, Cache, Lock, eventos, i18n, logger, hash, health, comandos Ace, deploy | `references/ecosystem.md` |

## Regras que evitam erros comuns

1. **Confirme a versão** (`@adonisjs/core` no `package.json`). Esta skill é **v6**. Se for v5, avise: a sintaxe é diferente (`@ioc:Adonis/...`, `Route`, `Database` globais).
2. **Nunca use imports da v5.** Na v6: `import router from '@adonisjs/core/services/router'`, `import db from '@adonisjs/lucid/services/db'`, `import env from '#start/env'`.
3. **Subpath imports** do `package.json`: `#controllers/*`, `#models/*`, `#validators/*`, `#services/*`, `#middleware/*`, `#policies/*`, `#start/*`, `#config/*`, `#exceptions/*`, `#listeners/*`, `#events/*`, `#abilities/*`, `#database/*`. Imports relativos em ESM exigem extensão `.js`.
4. **Gere arquivos com Ace** (`node ace make:*`) — nomes e locais corretos. Arquivos em **snake_case**: `posts_controller.ts`, `post.ts` (model singular).
5. **Instale pacotes com `node ace add <pacote>`** (configura provider, config, middleware). `npm i` sozinho não basta.
6. **Controllers lazy** nas rotas: `const X = () => import('#controllers/x_controller')`.
7. **Valide toda entrada com VineJS** e use o payload validado (nunca `request.all()` em `create/merge`).
8. **Env tipado** em `start/env.ts`; acesse via `env.get()`, nunca `process.env` direto.
9. **Lucid**: propriedades com `declare`, relações com `preload` em listas (evita N+1), `serializeAs: null` em campos sensíveis.
10. **Controllers finos**; regra de negócio em `app/services` (injetados com `@inject()`).
11. **Autorize recursos** (Bouncer) em todo endpoint com `:id`; autentique com `middleware.auth()`.
12. **Canais Transmit privados precisam de `transmit.authorize`**; são públicos por padrão.

## Criar projeto

```bash
npm init adonisjs@latest meu-app -- --kit=api   # web | api | hypermedia | inertia | slim
cd meu-app && node ace serve --hmr
```
`api` → JSON + access tokens · `web` → Edge + sessão · `inertia` → React/Vue/Svelte/Solid · `hypermedia` → Edge + Alpine/htmx · `slim` → mínimo.

## Estrutura

```
app/controllers  models  validators  services  middleware  policies  exceptions  listeners  events
config/          database/{migrations,seeders,factories}
start/{routes,kernel,env,transmit,events,limiter,view}.ts
resources/{views,js,lang}   tests/{unit,functional,browser}   bin/server.ts   adonisrc.ts
```
`adonisrc.ts` registra `providers`, `preloads`, `commands`, suites de teste e `metaFiles`.

## Comandos Ace essenciais

```bash
node ace make:controller posts -r        node ace make:model Post -m -c
node ace make:migration x [--alter]      node ace make:validator post
node ace make:middleware x               node ace make:service post_service
node ace make:policy post                node ace make:mail welcome
node ace make:event x / make:listener y  node ace make:command x
node ace make:factory Post               node ace make:seeder user
node ace make:test posts --suite=functional    node ace make:provider x
node ace list:routes                     node ace repl
node ace migration:run | rollback | fresh --seed | status
node ace db:seed                         node ace test [suite] [--files= --tests= --tags=]
node ace build                           node ace generate:key
```

## Fluxo padrão para uma feature CRUD (checklist)

1. `make:model Post -m` → colunas + relações (`references/lucid.md`).
2. Migration com FKs, índices e `down()`; `migration:run`.
3. `make:validator post` → `create` e `update` (`references/vinejs.md`).
4. `make:controller posts -r`; lógica pesada em service.
5. Rotas em `start/routes.ts` (`resource`, `.apiOnly()`, grupo + `middleware.auth()`).
6. Policy (`make:policy post`) e `bouncer.with(PostPolicy).authorize(...)` (`references/auth-bouncer.md`).
7. Factory + testes functional: feliz, 422, 401, 403, 404 (`references/japa-testing.md`).
8. Se precisar de tempo real: `transmit.broadcast` após persistir (`references/transmit.md`).

## Exemplo mínimo (API)

```ts
// start/routes.ts
import router from '@adonisjs/core/services/router'
import { middleware } from '#start/kernel'
const PostsController = () => import('#controllers/posts_controller')

router.group(() => {
  router.resource('posts', PostsController).apiOnly()
}).prefix('/api/v1').use(middleware.auth())

// app/controllers/posts_controller.ts
import type { HttpContext } from '@adonisjs/core/http'
import Post from '#models/post'
import PostPolicy from '#policies/post_policy'
import { createPostValidator } from '#validators/post'

export default class PostsController {
  async index({ request }: HttpContext) {
    return Post.query().preload('author').orderBy('createdAt', 'desc').paginate(request.input('page', 1), 20)
  }
  async store({ request, auth, response }: HttpContext) {
    const payload = await request.validateUsing(createPostValidator)
    const post = await Post.create({ ...payload, userId: auth.getUserOrFail().id })
    return response.created(post)
  }
  async destroy({ params, bouncer, response }: HttpContext) {
    const post = await Post.findOrFail(params.id)
    await bouncer.with(PostPolicy).authorize('delete', post)
    await post.delete()
    return response.noContent()
  }
}
```

## Quando houver dúvida

Na dúvida sobre uma API específica ou mudança de versão, consulte https://docs.adonisjs.com (e `https://lucid.adonisjs.com`, `https://vinejs.dev`, `https://japa.dev`) antes de afirmar. Pacotes de comunidade (scheduler, filas, soft delete) variam por versão — verifique compatibilidade.
