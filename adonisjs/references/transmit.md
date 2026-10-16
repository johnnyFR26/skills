# Transmit (tempo real via SSE) — AdonisJS v6

Transmit (`@adonisjs/transmit`) é o módulo oficial de **eventos em tempo real servidor → cliente usando Server-Sent Events (SSE)**. Comunicação é **unidirecional**: o cliente recebe pelo canal; para enviar dados ao servidor, use rotas HTTP normais. Não é WebSocket.

## Índice
1. Instalação · 2. Registrar rotas · 3. Canais e autorização · 4. Broadcast · 5. Cliente · 6. Eventos do servidor · 7. Multi-instância (Redis) · 8. Padrões (chat, notificações, progresso) · 9. Produção e armadilhas

## 1. Instalação
```bash
node ace add @adonisjs/transmit     # servidor
npm i @adonisjs/transmit-client      # cliente (front-end)
```
Cria `config/transmit.ts` e registra o provider. Config:
```ts
import { defineConfig } from '@adonisjs/transmit'
import { redis } from '@adonisjs/transmit/transports'

export default defineConfig({
  pingInterval: '1m',          // keep-alive; false desliga
  transport: null,             // ou { driver: redis({ host, port, password, keyPrefix: 'transmit' }) }
})
```

## 2. Registrar rotas
Em `start/routes.ts`:
```ts
import transmit from '@adonisjs/transmit/services/main'
transmit.registerRoutes()
```
Expõe `__transmit/events` (stream SSE), `__transmit/subscribe` e `__transmit/unsubscribe`. Para exigir/ler a sessão nas rotas:
```ts
import { middleware } from '#start/kernel'
transmit.registerRoutes((route) => {
  // silentAuth: identifica o usuário se houver sessão, sem bloquear anônimos
  if (route.getPattern() === '__transmit/events') return   // stream pode ser público
  route.middleware(middleware.silentAuth())
})
```
Use `silentAuth` (ou o guard adequado) nas rotas de subscribe para que `ctx.auth.user` exista dentro do `authorize`.
**CORS**: se o front estiver em outra origem, habilite `@adonisjs/cors` com `credentials: true` e origem explícita.

## 3. Canais e autorização
Canais são strings (`chats/1/messages`, `users/42/notifications`). **Canais são públicos por padrão** — proteja os privados com `authorize`. Crie `start/transmit.ts` (registre em `preloads` do `adonisrc.ts`):
```ts
import transmit from '@adonisjs/transmit/services/main'
import type { HttpContext } from '@adonisjs/core/http'
import Chat from '#models/chat'

transmit.authorize<{ id: string }>('users/:id/notifications', (ctx: HttpContext, { id }) => {
  return ctx.auth.user?.id === Number(id)
})

transmit.authorize<{ id: string }>('chats/:id/messages', async (ctx: HttpContext, { id }) => {
  const user = ctx.auth.user
  if (!user) return false
  const chat = await Chat.find(id)
  return !!chat && (await chat.related('members').query().where('users.id', user.id).first()) !== null
})
```
Retornar `false` → 403 no subscribe. Parâmetros `:id` chegam como string. Canais sem regra de `authorize` aceitam qualquer um.

## 4. Broadcast
```ts
import transmit from '@adonisjs/transmit/services/main'

transmit.broadcast('chats/1/messages', { id: msg.id, text: msg.text, author: user.name })
transmit.broadcast('global', { type: 'maintenance', at: Date.now() })
```
- Payload deve ser serializável em JSON.
- Faça o broadcast **depois** de persistir (e após commit da transação).
- Para não ecoar ao remetente, passe os UIDs a excluir (veja a documentação da sua versão do pacote: `broadcastExcept`/`excludeUid`).
- Pode ser chamado de controllers, listeners de eventos, jobs e comandos Ace.

## 5. Cliente
```ts
import { Transmit } from '@adonisjs/transmit-client'

export const transmit = new Transmit({
  baseUrl: window.location.origin,
  // maxReconnectAttempts: 5,
  // beforeSubscribe: (req) => { (req as any).headers... }   // p/ cabeçalhos custom (ex.: bearer)
  // onReconnectAttempt: (n) => {}, onReconnectFailed: () => {},
  // onSubscribeFailed: (res) => {}, onSubscription: (ch) => {}, onUnsubscription: (ch) => {},
})

const sub = transmit.subscription('chats/1/messages')
sub.onMessage<{ text: string }>((data) => console.log(data.text))
await sub.create()          // inscreve (só após isso recebe mensagens)
// ...
await sub.delete()          // cancela inscrição

// atalho: assina e escuta
const unsubscribe = transmit.listenOn<{ text: string }>('global', (d) => {})
```
Estado da conexão: `transmit.on('connected' | 'disconnected' | 'reconnecting', cb)`.
Um `Transmit` por aba/app (singleton); várias `subscription` compartilham a mesma conexão SSE.
Cookies de sessão vão automaticamente no mesmo domínio; cross-origin exige `credentials` + CORS.

### Exemplo React
```tsx
useEffect(() => {
  const sub = transmit.subscription(`chats/${chatId}/messages`)
  sub.onMessage((m: Message) => setMessages((prev) => [...prev, m]))
  sub.create()
  return () => { sub.delete() }
}, [chatId])
```
Com Inertia/Edge, importe o client no bundle (Vite) normalmente.

## 6. Eventos do servidor
```ts
transmit.on('connect', ({ uid }) => {})
transmit.on('disconnect', ({ uid }) => {})
transmit.on('subscribe', ({ uid, channel }) => {})
transmit.on('unsubscribe', ({ uid, channel }) => {})
transmit.on('broadcast', ({ channel, payload }) => {})
```
Úteis para presença online, métricas e auditoria.

## 7. Multi-instância (Redis)
Com mais de um processo/servidor, o broadcast de uma instância não alcança clientes de outra, a menos que use transporte Redis:
```bash
node ace add @adonisjs/redis
```
```ts
transport: { driver: redis({ host: env.get('REDIS_HOST'), port: env.get('REDIS_PORT'), password: env.get('REDIS_PASSWORD'), keyPrefix: 'transmit' }) }
```

## 8. Padrões
**Chat:** `POST /chats/:id/messages` valida → salva → `transmit.broadcast(`chats/${id}/messages`, msg.serialize())` → responde 201. Cliente assina o canal e renderiza.
**Notificações por usuário:** canal `users/:id/notifications` com `authorize` por dono; broadcast a partir de listeners (`emitter.on('order:paid', ...)`).
**Progresso de job/upload:** canal `jobs/:id/progress`; job faz `transmit.broadcast` a cada etapa; cliente fecha a assinatura ao receber `{ done: true }`.
**Dashboard ao vivo:** comando/scheduler publica métricas em `metrics/global` a cada N segundos.
Mensagens perdidas durante reconexão não são reenviadas: ao reconectar, **recarregue o estado via HTTP** e use o canal só para deltas.

## 9. Produção e armadilhas
- **Proxy reverso (Nginx):** desative buffering para o stream: `proxy_buffering off; proxy_read_timeout 1h;` e preserve `Connection`/headers; sem isso as mensagens atrasam.
- **HTTP/1.1** limita ~6 conexões por domínio; prefira HTTP/2 ou um único `Transmit` por aba.
- Mantenha `pingInterval` abaixo do timeout de ociosidade do balanceador.
- Não envie dados sensíveis em canais públicos; autorize **sempre** canais privados.
- Não inclua o model inteiro: serialize só o necessário (`serializeAs: null` não é aplicado a objetos que você monta manualmente).
- Sem Redis em cluster = mensagens só chegam a parte dos clientes.
- Para comunicação bidirecional de baixa latência (jogos), considere WebSocket (ex.: `socket.io`/`ws` via provider próprio).
