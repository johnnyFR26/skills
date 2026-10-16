# Ecossistema AdonisJS v6 — pacotes e recursos adicionais

Instale sempre com `node ace add <pacote>` (instala, configura e registra providers/middleware).

## Índice
Session · Shield · CORS · Drive (arquivos) · Mail · Limiter · Redis · Cache · Lock · Events · i18n · Logger · Hash · Encryption · Health checks · Comandos Ace custom · Scheduler e filas (comunidade) · Static · REPL · Build e deploy · Checklist de produção

## Session (`@adonisjs/session`)
Drivers: `cookie` (padrão), `file`, `redis`, `database`, `memory` (testes). Config em `config/session.ts`.
```ts
session.put('cart', [1, 2]); session.get('cart', []); session.has('cart'); session.forget('cart'); session.pull('k')
session.flash('success', 'Salvo!')          // vale só para a próxima requisição
session.flashAll(); session.flashErrors({...}); session.flashMessages.get('success')
await session.regenerate()                  // após login (evita session fixation)
```
Para múltiplas instâncias use `redis` ou `database` (cookie driver só guarda dados pequenos).

## Shield (`@adonisjs/shield`)
CSRF, CSP, HSTS, X-Frame-Options, nosniff. Config `config/shield.ts`. Em forms Edge: `{{ csrfField() }}`. Para APIs com token bearer desative CSRF (`csrf: { enabled: false }`) ou exclua rotas com `exceptRoutes`. Em testes, `.withCsrfToken()` no client.

## CORS (`@adonisjs/cors`)
`config/cors.ts`: `enabled`, `origin` (array/função/`true`), `methods`, `headers`, `credentials`, `maxAge`. Com cookies/Transmit cross-origin: `credentials: true` e origem **explícita** (nunca `*`).

## Drive (`@adonisjs/drive`, FlyDrive)
Discos: `fs` (local), `s3`, `gcs`, `r2`, `spaces`. Config `config/drive.ts`.
```ts
import drive from '@adonisjs/drive/services/main'
const disk = drive.use()                 // disco padrão; drive.use('s3')
await disk.put('avatars/a.png', buffer, { contentType: 'image/png' })
await disk.putStream(key, readable)
await disk.moveFromFs(file.tmpPath!, key)          // do arquivo enviado
const url = await disk.getUrl(key)                 // público
const signed = await disk.getSignedUrl(key, { expiresIn: '10m' })   // privado
await disk.exists(key); await disk.delete(key); await disk.get(key); await disk.getStream(key)
```
Salve a **chave** no banco, não a URL. Valide extensão/tamanho com VineJS. Nunca use nome de arquivo enviado pelo usuário (use `cuid()`).

## Mail (`@adonisjs/mail`)
Mailers: `smtp`, `ses`, `mailgun`, `sparkpost`, `resend`, `brevo`. Config `config/mail.ts`.
```bash
node ace make:mail welcome --kind=notification
```
```ts
import { BaseMail } from '@adonisjs/mail'
export default class WelcomeNotification extends BaseMail {
  subject = 'Bem-vindo!'
  constructor(private user: User) { super() }
  prepare() {
    this.message.to(this.user.email).from('no-reply@app.com', 'App').htmlView('emails/welcome', { user: this.user })
  }
}
import mail from '@adonisjs/mail/services/main'
await mail.send(new WelcomeNotification(user))
await mail.sendLater(new WelcomeNotification(user))   // enfileira (messenger/queue)
```
Templates Edge em `resources/views/emails/`. Em testes use `mail.fake()`.

## Limiter (`@adonisjs/limiter`)
Stores: `redis`, `database`, `memory`. Defina throttles em `start/limiter.ts`:
```ts
import limiter from '@adonisjs/limiter/services/main'
export const throttle = limiter.define('global', () => limiter.allowRequests(60).every('1 minute'))
export const loginThrottle = limiter.define('login', (ctx) =>
  limiter.allowRequests(5).every('1 minute').blockFor('10 mins').usingKey(`${ctx.request.ip()}_${ctx.request.input('email')}`))
// rotas
router.post('/login', ...).use(loginThrottle)
router.use([() => import('#middleware/...')])  // ou aplique `throttle` globalmente em router.use
```
Uso manual: `const l = limiter.use({ requests: 3, duration: '1 min' }); await l.attempt('key', async () => {...})`. Resposta de excesso: 429 (`E_TOO_MANY_REQUESTS`).

## Redis (`@adonisjs/redis`)
```ts
import redis from '@adonisjs/redis/services/main'
await redis.set('k', 'v', 'EX', 60); await redis.get('k'); await redis.del('k')
await redis.hset('user:1', { name: 'A' }); await redis.publish('canal', JSON.stringify(x))
redis.subscribe('canal', (msg) => {})
redis.connection('cache').get('x')       // múltiplas conexões em config/redis.ts
```
Base para session, limiter, cache, Transmit multi-instância e filas.

## Cache (`@adonisjs/cache`, Bentocache)
```ts
import cache from '@adonisjs/cache/services/main'
const posts = await cache.getOrSet({ key: 'posts:home', ttl: '5m', factory: () => Post.query().limit(10) })
await cache.set({ key: 'k', value: 1, ttl: '1h' }); await cache.get({ key: 'k' }); await cache.delete({ key: 'k' })
const users = cache.namespace('users')
await cache.getOrSet({ key: 'x', tags: ['posts'], ttl: '1h', factory })
await cache.deleteByTag({ tags: ['posts'] })
```
Camadas L1 (memória) + L2 (redis/db); proteção contra *cache stampede* embutida. Invalide no `@afterSave/@afterDelete` do model.

## Lock (`@adonisjs/lock`)
Locks distribuídos (Verrou): `await lock.createLock('invoice:42').run(async () => {...})` ou `acquire()/release()`. Use para evitar processamento duplicado (jobs, pagamentos).

## Events (`emitter`)
Eventos tipados:
```ts
// start/events.ts (preload)
import emitter from '@adonisjs/core/services/emitter'
declare module '@adonisjs/core/types' { interface EventsList { 'user:registered': User } }
emitter.on('user:registered', async (user) => { await mail.send(new WelcomeNotification(user)) })
await emitter.emit('user:registered', user)       // aguarda listeners
```
Baseado em classes:
```bash
node ace make:event user_registered ; node ace make:listener send_welcome --event=user_registered
```
```ts
emitter.listen(UserRegistered, [() => import('#listeners/send_welcome')])
UserRegistered.dispatch(user)
```
Eventos de Lucid: `db:query`. Em testes: `emitter.fake()`.

## i18n (`@adonisjs/i18n`)
Arquivos `resources/lang/pt/messages.json` (ICU). `i18n.t('messages.hello', { name })`; no Edge `{{ t('messages.hello') }}`; `ctx.i18n.locale`. Detecção por `Accept-Language` via middleware `detect_user_locale`. Mensagens de validação: `resources/lang/<locale>/validator.json`. Formatação: `i18n.formatNumber`, `formatCurrency`, `formatDate`.

## Logger (Pino)
```ts
ctx.logger.info({ userId: 1 }, 'login ok')       // inclui request id
import logger from '@adonisjs/core/services/logger'
logger.child({ service: 'billing' }).error(err, 'falhou')
```
`config/logger.ts`: `level` via env, `redact` para campos sensíveis (`['password','token']`), `pino-pretty` só em dev.

## Hash
```ts
import hash from '@adonisjs/core/services/hash'
const h = await hash.make('senha')          // scrypt (padrão); argon2/bcrypt configuráveis em config/hash.ts
await hash.verify(h, 'senha')               // (hash, texto-plano) — ordem importa
hash.needsReHash(h)
```
## Encryption
`import encryption from '@adonisjs/core/services/encryption'` → `encryption.encrypt(valor, '1h')`, `encryption.decrypt(payload)`; depende do `APP_KEY`.

## Health checks
```ts
// start/health.ts
import { HealthChecks, DiskSpaceCheck, MemoryHeapCheck } from '@adonisjs/core/health'
import { DbCheck } from '@adonisjs/lucid/database'
import db from '@adonisjs/lucid/services/db'
export const healthChecks = new HealthChecks().register([new DiskSpaceCheck(), new MemoryHeapCheck(), new DbCheck(db.connection())])
// routes
router.get('/health', async ({ response }) => {
  const report = await healthChecks.run()
  return report.isHealthy ? response.ok(report) : response.serviceUnavailable(report)
})
```
Use como liveness/readiness em Kubernetes/ELB; proteja detalhes com token se expostos publicamente.

## Comandos Ace customizados
```bash
node ace make:command digest_send
```
```ts
import { BaseCommand, args, flags } from '@adonisjs/core/ace'
import type { CommandOptions } from '@adonisjs/core/types/ace'
export default class DigestSend extends BaseCommand {
  static commandName = 'digest:send'
  static description = 'Envia o resumo diário'
  static options: CommandOptions = { startApp: true }       // necessário para usar DB, containers, etc.
  @args.string({ description: 'Segmento' }) declare segment: string
  @flags.boolean({ alias: 'd' }) declare dryRun: boolean
  async run() {
    this.logger.info(`Enviando para ${this.segment}`)
    const spinner = this.logger.info('ok')
    if (this.dryRun) return
  }
}
```
Rodar: `node ace digest:send vip --dry-run`. Em produção: `node build/ace.js digest:send`. Prompts: `await this.prompt.ask('Nome?')`, `this.prompt.confirm()`; `this.exitCode = 1` para falha.

## Scheduler e filas (pacotes da comunidade — confirme compatibilidade com a sua versão)
- **Agendamento**: `adonisjs-scheduler` (`node ace scheduler:run`, `scheduler:work`); alternativa: cron do SO chamando um comando Ace.
- **Filas**: `@rlanz/bull-queue` (BullMQ + Redis) com `node ace queue:listen`; ou `adonisjs-jobs`. Jobs devem ser **idempotentes**, com retries e backoff.
- Para tarefas simples pós-resposta: `emitter` + listeners (não são duráveis; use fila quando precisar de garantia).

## Static e uploads
`config/static.ts` serve `public/`. Arquivos enviados pelo usuário **não** devem ir para `public/` sem validação; prefira Drive com URLs assinadas.

## REPL
`node ace repl` → `await loadModels()`, `await loadServices()`, `await loadHelpers()`; explore models e serviços interativamente.

## Build e deploy
```bash
node ace build                     # gera ./build (JS compilado)
cd build && npm ci --omit=dev
node ace migration:run --force     # (ou node ace.js migration:run --force dentro de build)
node bin/server.js
```
- Defina `NODE_ENV=production`, `APP_KEY`, `HOST=0.0.0.0`, `PORT`, banco, Redis, mail, `LOG_LEVEL`.
- Docker: multi-stage (builder roda `node ace build`; imagem final copia `build/` e instala deps de produção); healthcheck em `/health`.
- Atrás de proxy: confie no proxy (`http.trustProxy` em `config/app.ts`) para IP/HTTPS corretos; cookies `secure`.
- Várias instâncias → session/cache/limiter/Transmit em Redis.
- Vite: `npm run build` já executado por `node ace build` quando há assets.

## Checklist de produção
1. `APP_KEY` e segredos fora do repositório · 2. `debug` desligado · 3. Migrations com `--force` no deploy · 4. CORS/Shield revisados · 5. Rate limit em login/APIs públicas · 6. Logs com `redact` · 7. Health check e métricas · 8. Backups do banco · 9. Redis para recursos compartilhados · 10. Testes verdes no CI (`node ace test`).
