# Receitas AdonisJS v6

## Upload de arquivos
```ts
import app from '@adonisjs/core/services/app'
import { cuid } from '@adonisjs/core/helpers'

const avatar = request.file('avatar', { size: '2mb', extnames: ['jpg', 'png'] })
if (!avatar) return response.badRequest('Arquivo ausente')
await avatar.move(app.makePath('storage/uploads'), { name: `${cuid()}.${avatar.extname}` })
```
Para S3/GCS use Drive: `node ace add @adonisjs/drive`.

## Eventos
```bash
node ace make:event user_registered
node ace make:listener send_welcome_email --event=user_registered
```
Dispare com `emitter.emit(UserRegistered, new UserRegistered(user))` (`import emitter from '@adonisjs/core/services/emitter'`).

## E-mail
`node ace add @adonisjs/mail`, depois `node ace make:mail welcome --kind=notification`. Envie com `mail.send(new WelcomeNotification(user))`.

## CORS
`node ace add @adonisjs/cors` e ajuste `config/cors.ts` (`origin`, `credentials`).

## Rate limit
`node ace add @adonisjs/limiter`; crie um throttle em `start/limiter.ts` e aplique via `middleware.throttle()` nas rotas.

## Tratamento de erros
Edite `app/exceptions/handler.ts` (`ExceptionHandler`): sobrescreva `handle()` para formato de erro customizado e `report()` para logging.
Exceptions próprias: `node ace make:exception PaymentFailed` (estende `Exception`, define `status` e `code`).

## Seeds e factories
```ts
// database/factories/post_factory.ts
export const PostFactory = factory.define(Post, ({ faker }) => ({ title: faker.lorem.sentence() })).build()
```
Use em seeders: `await PostFactory.createMany(20)`.

## Deploy
1. `node ace build`
2. Copie `build/`, instale deps de produção: `npm ci --omit=dev` dentro de `build/`
3. Defina env (`NODE_ENV=production`, `APP_KEY`, banco, `HOST`, `PORT`)
4. `node ace migration:run --force`
5. `node bin/server.js`
