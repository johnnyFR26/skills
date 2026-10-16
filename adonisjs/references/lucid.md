# Lucid ORM (AdonisJS v6)

## Índice
1. Instalação e config · 2. Models e colunas · 3. Queries · 4. Escrita (CRUD) · 5. Relações · 6. Scopes e hooks · 7. Serialização · 8. Transações · 9. Migrations · 10. Seeders e Factories · 11. Debug e dicas

## 1. Instalação e config
```bash
node ace add @adonisjs/lucid        # pergunta o dialeto (sqlite, pg, mysql, mssql, libsql)
```
- Config em `config/database.ts`; credenciais em `.env` (`DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_DATABASE`).
- Várias conexões: defina em `connections` e use `static connection = 'outra'` no model ou `db.connection('outra')`.
- Use `useTz: true` em colunas timestamp no Postgres quando precisar de timezone.

## 2. Models e colunas
```ts
import { DateTime } from 'luxon'
import { BaseModel, column, computed, beforeCreate } from '@adonisjs/lucid/orm'
import { randomUUID } from 'node:crypto'

export default class Product extends BaseModel {
  static table = 'products'            // opcional (padrão: plural snake_case)
  static selfAssignPrimaryKey = true   // necessário para UUID gerado no app

  @column({ isPrimary: true }) declare id: string
  @column() declare name: string
  @column({ columnName: 'unit_price' }) declare price: number
  @column({ serializeAs: null }) declare internalNotes: string | null
  @column.date() declare releasedOn: DateTime | null
  @column.dateTime({ autoCreate: true }) declare createdAt: DateTime
  @column.dateTime({ autoCreate: true, autoUpdate: true }) declare updatedAt: DateTime | null

  // conversão custom
  @column({
    prepare: (v: string[]) => JSON.stringify(v),
    consume: (v: string) => (typeof v === 'string' ? JSON.parse(v) : v),
  })
  declare tags: string[]

  @computed() get label() { return `${this.name} (${this.price})` }

  @beforeCreate()
  static assignUuid(p: Product) { p.id = randomUUID() }
}
```
Regras: sempre `declare` (nunca inicialize); propriedade camelCase ↔ coluna snake_case automaticamente; `DateTime` é Luxon.

## 3. Queries
```ts
await Post.all()
await Post.find(1)                       // null se não existir
await Post.findOrFail(1)                 // 404 automático
await Post.findBy('slug', 'ola')
await Post.findManyBy('status', 'draft')
await Post.firstOrFail()

await Post.query()
  .where('status', 'published')
  .andWhere((q) => q.where('views', '>', 100).orWhereNull('featuredAt'))
  .whereIn('userId', [1, 2])
  .whereNot('title', 'x')
  .whereLike('title', '%adonis%')        // use whereILike p/ case-insensitive (pg)
  .whereBetween('views', [10, 100])
  .whereHas('comments', (q) => q.where('approved', true))
  .orWhereDoesntHave('comments')
  .orderBy('createdAt', 'desc')
  .limit(10).offset(20)
  .select('id', 'title')

// condicional sem if/else
Post.query().if(search, (q) => q.whereILike('title', `%${search}%`))
Post.query().unless(isAdmin, (q) => q.where('public', true))

// agregados
const total = await Post.query().count('* as total').first()
total?.$extras.total
await Post.query().withCount('comments')           // post.$extras.comments_count
await Post.query().withAggregate('comments', (q) => q.max('createdAt').as('lastCommentAt'))

// paginação
const page = await Post.query().paginate(request.input('page', 1), 20)
page.baseUrl('/posts')
return page.serialize() // { meta: {total, perPage, currentPage, lastPage,...}, data: [...] }

// locks / raw
Post.query().forUpdate()
Post.query().whereRaw('lower(title) = ?', ['x'])
import db from '@adonisjs/lucid/services/db'
await db.from('posts').where('id', 1).first()      // query builder puro (sem model)
await db.rawQuery('select now()')
```
Para grandes volumes use `.knexQuery`/`db.from` com `select` específico e evite carregar relações desnecessárias.

## 4. Escrita (CRUD)
```ts
const post = await Post.create({ title: 'Oi' })
await Post.createMany([{ title: 'a' }, { title: 'b' }])

post.merge({ title: 'Novo' })   // atribui só campos fornecidos
await post.save()               // INSERT se novo, UPDATE só dos campos alterados
await post.delete()

await Post.firstOrCreate({ slug: 'x' }, { title: 'X' })   // (busca, dados p/ criar)
await Post.updateOrCreate({ slug: 'x' }, { title: 'Y' })
await Post.updateOrCreateMany('slug', [{ slug: 'a', title: 'A' }])

// bulk (não dispara hooks do model)
await Post.query().where('status', 'draft').update({ status: 'archived' })
await Post.query().where('createdAt', '<', cutoff).delete()

post.$isPersisted; post.$dirty; post.$original
```
Nunca passe `request.all()` direto: valide com VineJS e use o payload validado (evita mass assignment).

## 5. Relações
```ts
import { belongsTo, hasOne, hasMany, manyToMany, hasManyThrough } from '@adonisjs/lucid/orm'
import type { BelongsTo, HasOne, HasMany, ManyToMany, HasManyThrough } from '@adonisjs/lucid/types/relations'

// User
@hasOne(() => Profile) declare profile: HasOne<typeof Profile>
@hasMany(() => Post) declare posts: HasMany<typeof Post>
@manyToMany(() => Role, { pivotTable: 'role_user', pivotTimestamps: true, pivotColumns: ['assigned_by'] })
declare roles: ManyToMany<typeof Role>
@hasManyThrough([() => Comment, () => Post]) declare comments: HasManyThrough<typeof Comment>

// Post
@belongsTo(() => User) declare author: BelongsTo<typeof User>
```
Chaves padrão: `localKey = id`, `foreignKey = <model>Id`. Customize: `@hasMany(() => Post, { foreignKey: 'authorId', localKey: 'id' })`.

Uso:
```ts
await Post.query().preload('author').preload('comments', (q) => q.where('approved', true).orderBy('id'))
await post.load('author')                 // lazy load
await post.loadCount('comments')
const comments = await post.related('comments').query().where('approved', true)

await user.related('posts').create({ title: 'x' })          // seta FK automaticamente
await user.related('posts').createMany([...])

// manyToMany
await user.related('roles').attach([1, 2])
await user.related('roles').attach({ 1: { assigned_by: 9 } })
await user.related('roles').detach([2])
await user.related('roles').sync([1, 3])            // deixa só 1 e 3
await user.related('roles').sync([1, 3], false)     // sem detach
```
Preload aninhado: `.preload('posts', (q) => q.preload('comments'))`. **Sempre `preload` em listas** para evitar N+1.

## 6. Scopes e hooks
```ts
import { scope, beforeSave, afterCreate, beforeFind, beforeFetch } from '@adonisjs/lucid/orm'
import type { ModelQueryBuilderContract } from '@adonisjs/lucid/types/model'

static published = scope((q) => q.where('status', 'published'))
static byAuthor = scope((q, userId: number) => q.where('userId', userId))
// uso
Post.query().apply((s) => s.published()).apply((s) => s.byAuthor(1))

@beforeSave()
static async hashPassword(user: User) {
  if (user.$dirty.password) user.password = await hash.make(user.password)
}
@beforeFind() @beforeFetch()
static ignoreDeleted(q: ModelQueryBuilderContract<typeof Post>) { q.whereNull('deleted_at') }
```
Hooks disponíveis: `before/after` `Create|Update|Save|Delete|Find|Fetch|Paginate`. Hooks **não** rodam em `query().update()/delete()`.
Soft delete não é nativo — use `adonis-lucid-soft-deletes` (comunidade) ou implemente com coluna `deleted_at` + `@beforeFind/@beforeFetch`.

## 7. Serialização
```ts
post.serialize()                                     // objeto puro (snake_case)
post.serialize({
  fields: { pick: ['id', 'title'] },                 // ou omit
  relations: { author: { fields: { pick: ['id', 'name'] } } },
})
```
- `serializeAs: 'novo_nome'` renomeia; `serializeAs: null` oculta (senhas!).
- Retornar model/array/paginator do controller serializa sozinho.
- Para DTOs estáveis de API, monte o objeto explicitamente em vez de expor o model.

## 8. Transações
```ts
import db from '@adonisjs/lucid/services/db'

await db.transaction(async (trx) => {               // commit/rollback automáticos
  const order = await Order.create({ total }, { client: trx })
  await order.related('items').createMany(items)   // herda a trx do order
  await Stock.query({ client: trx }).where('id', 1).decrement('qty', 1)
})
// manual
const trx = await db.transaction()
try { /* ... */ await trx.commit() } catch (e) { await trx.rollback(); throw e }
// instância existente
user.useTransaction(trx)
```
Exceções dentro do callback fazem rollback e são relançadas.

## 9. Migrations
```bash
node ace make:migration create_posts_table
node ace make:migration add_slug_to_posts --alter
node ace migration:run | migration:rollback [--batch=0] | migration:fresh [--seed] | migration:refresh | migration:reset | migration:status
node ace migration:run --force      # produção
node ace db:wipe
```
```ts
import { BaseSchema } from '@adonisjs/lucid/schema'
export default class extends BaseSchema {
  protected tableName = 'posts'
  async up() {
    this.schema.createTable(this.tableName, (t) => {
      t.increments('id')                      // ou t.uuid('id').primary().defaultTo(this.raw('gen_random_uuid()'))
      t.integer('user_id').unsigned().notNullable().references('users.id').onDelete('CASCADE')
      t.string('title', 120).notNullable()
      t.string('slug').unique()
      t.text('body')
      t.boolean('published').defaultTo(false)
      t.jsonb('meta')
      t.enum('status', ['draft', 'published']).defaultTo('draft')
      t.index(['user_id', 'created_at'])
      t.timestamp('created_at', { useTz: true }).notNullable().defaultTo(this.now())
      t.timestamp('updated_at', { useTz: true })
    })
  }
  async down() { this.schema.dropTable(this.tableName) }
}
```
Alterações: `this.schema.alterTable(name, t => { t.string('slug'); t.dropColumn('old'); t.renameColumn('a','b') })`.
Dados na migration: `this.defer(async (db) => { await db.table('roles').insert({ name: 'admin' }) })`.
Regras: não edite migration já aplicada em produção; sempre escreva `down()`; chaves estrangeiras com `unsigned()` coerente com o tipo da PK.

## 10. Seeders e Factories
```bash
node ace make:seeder user ; node ace make:factory User
node ace db:seed [--files=./database/seeders/user_seeder.ts]
```
```ts
// database/factories/user_factory.ts
import factory from '@adonisjs/lucid/factories'
import User from '#models/user'
import { PostFactory } from '#database/factories/post_factory'

export const UserFactory = factory
  .define(User, async ({ faker }) => ({
    fullName: faker.person.fullName(),
    email: faker.internet.email(),
    password: 'secret123',
  }))
  .state('admin', (u) => (u.role = 'admin'))
  .relation('posts', () => PostFactory)
  .build()

// uso
await UserFactory.create()
await UserFactory.apply('admin').with('posts', 3).createMany(5)
await UserFactory.merge({ email: 'a@b.c' }).create()
UserFactory.make()      // não persiste
```
Seeder: `export default class extends BaseSeeder { async run() { await UserFactory.createMany(10) } }`. Em seeders por ambiente use `static environment = ['development']`.

## 11. Debug e dicas
- Ver SQL: `debug: true` na conexão em `config/database.ts`, e em `start/` / provider: `emitter.on('db:query', db.prettyPrint)` (`@adonisjs/core/services/emitter`).
- `query.toSQL().toNative()` mostra SQL + bindings sem executar.
- Evite `Model.all()` em tabelas grandes; use `paginate`/`select`.
- Em testes, use `testUtils.db().withGlobalTransaction()` para isolar dados.
- Colunas Postgres JSON: use `jsonb`; o `consume` pode receber string ou objeto dependendo do driver — trate os dois.
