# Banco de Dados NestJS — TypeORM & Prisma

## TypeORM

### Configuração (App Module)

```typescript
TypeOrmModule.forRootAsync({
  imports: [ConfigModule],
  inject: [ConfigService],
  useFactory: (config: ConfigService): TypeOrmModuleOptions => ({
    type: 'postgres',
    url: config.get('DATABASE_URL'),
    entities: [__dirname + '/**/*.entity{.ts,.js}'],
    migrations: [__dirname + '/migrations/*{.ts,.js}'],
    synchronize: config.get('NODE_ENV') === 'development', // NUNCA em produção
    logging: config.get('NODE_ENV') === 'development',
    ssl: config.get('NODE_ENV') === 'production' ? { rejectUnauthorized: false } : false,
  }),
}),
```

### Entidade com Relacionamentos

```typescript
@Entity('products')
export class Product {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  name: string;

  @Column({ type: 'decimal', precision: 10, scale: 2 })
  price: number;

  @Column({ type: 'int', default: 0 })
  stock: number;

  // Índice para buscas frequentes
  @Index()
  @Column({ length: 50 })
  category: string;

  // ManyToOne com FK
  @ManyToOne(() => Supplier, (supplier) => supplier.products, {
    onDelete: 'SET NULL',
    nullable: true,
    eager: false,   // false = carregue explicitamente com relations
  })
  @JoinColumn({ name: 'supplier_id' })
  supplier?: Supplier;

  // OneToMany
  @OneToMany(() => OrderItem, (item) => item.product)
  orderItems: OrderItem[];

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;

  @DeleteDateColumn()  // soft delete
  deletedAt?: Date;
}
```

### Padrão Repository Customizado

```typescript
@Injectable()
export class ProductsRepository extends Repository<Product> {
  constructor(
    @InjectRepository(Product)
    private readonly repo: Repository<Product>,
  ) {
    super(repo.target, repo.manager, repo.queryRunner);
  }

  async findWithFilters(filters: FilterProductDto): Promise<[Product[], number]> {
    const qb = this.repo
      .createQueryBuilder('p')
      .leftJoinAndSelect('p.supplier', 's')
      .where('p.deletedAt IS NULL');

    if (filters.category) {
      qb.andWhere('p.category = :category', { category: filters.category });
    }

    if (filters.minPrice) {
      qb.andWhere('p.price >= :minPrice', { minPrice: filters.minPrice });
    }

    return qb
      .orderBy('p.createdAt', 'DESC')
      .take(filters.limit ?? 20)
      .skip(filters.offset ?? 0)
      .getManyAndCount();
  }
}
```

### Transactions

```typescript
// No service — usando DataSource
constructor(private readonly dataSource: DataSource) {}

async transfer(from: string, to: string, amount: number) {
  const queryRunner = this.dataSource.createQueryRunner();
  await queryRunner.connect();
  await queryRunner.startTransaction();

  try {
    await queryRunner.manager.decrement(Account, { id: from }, 'balance', amount);
    await queryRunner.manager.increment(Account, { id: to }, 'balance', amount);

    await queryRunner.commitTransaction();
  } catch (err) {
    await queryRunner.rollbackTransaction();
    throw new InternalServerErrorException('Falha na transferência');
  } finally {
    await queryRunner.release();
  }
}
```

### Migrations

```bash
# Gerar migration
npx typeorm migration:generate -d src/config/data-source.ts src/migrations/AddProductStock

# Rodar migrations
npx typeorm migration:run -d src/config/data-source.ts

# Reverter
npx typeorm migration:revert -d src/config/data-source.ts
```

```typescript
// data-source.ts — usado pelo TypeORM CLI
export const AppDataSource = new DataSource({
  type: 'postgres',
  url: process.env.DATABASE_URL,
  entities: ['src/**/*.entity.ts'],
  migrations: ['src/migrations/*.ts'],
});
```

---

## Prisma

### Setup

```bash
npm i @prisma/client
npm i -D prisma
npx prisma init
```

### Schema (schema.prisma)

```prisma
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

generator client {
  provider = "prisma-client-js"
}

model User {
  id        String    @id @default(uuid())
  name      String    @db.VarChar(100)
  email     String    @unique
  password  String
  role      Role      @default(USER)
  isActive  Boolean   @default(true)
  createdAt DateTime  @default(now())
  updatedAt DateTime  @updatedAt
  deletedAt DateTime?

  posts Post[]

  @@index([email])
  @@map("users")
}

enum Role {
  USER
  ADMIN
}
```

### Prisma Service

```typescript
@Injectable()
export class PrismaService extends PrismaClient implements OnModuleInit {
  async onModuleInit() {
    await this.$connect();
  }

  // Habilitar soft delete em todas as queries
  async enableShutdownHooks(app: INestApplication) {
    this.$on('beforeExit', async () => {
      await app.close();
    });
  }
}
```

### Uso no Service

```typescript
@Injectable()
export class UsersService {
  constructor(private prisma: PrismaService) {}

  async findMany(dto: FilterUsersDto) {
    const [users, total] = await this.prisma.$transaction([
      this.prisma.user.findMany({
        where: {
          deletedAt: null,
          role: dto.role,
          name: dto.search ? { contains: dto.search, mode: 'insensitive' } : undefined,
        },
        select: { id: true, name: true, email: true, role: true },
        orderBy: { createdAt: 'desc' },
        skip: dto.offset ?? 0,
        take: dto.limit ?? 20,
      }),
      this.prisma.user.count({ where: { deletedAt: null } }),
    ]);
    return { data: users, total };
  }
}
```

### Migrations Prisma

```bash
npx prisma migrate dev --name init       # desenvolvimento
npx prisma migrate deploy                # produção
npx prisma studio                        # interface visual
npx prisma db seed                       # rodar seed
```

---

## Paginação Genérica

```typescript
// pagination.dto.ts
export class PaginationDto {
  @IsOptional() @IsInt() @Min(1)
  @Type(() => Number)
  page?: number = 1;

  @IsOptional() @IsInt() @Min(1) @Max(100)
  @Type(() => Number)
  limit?: number = 20;

  get skip() { return (this.page - 1) * this.limit; }
}

// paginated-response.dto.ts
export class PaginatedResponseDto<T> {
  data: T[];
  meta: { total: number; page: number; limit: number; totalPages: number };

  static of<T>(data: T[], total: number, dto: PaginationDto) {
    return {
      data,
      meta: {
        total,
        page: dto.page,
        limit: dto.limit,
        totalPages: Math.ceil(total / dto.limit),
      },
    };
  }
}
```