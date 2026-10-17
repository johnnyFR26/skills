---
name: nestjs-development
description: >
  Guia completo para desenvolvimento em NestJS com TypeScript. Use esta skill sempre que o usuário mencionar NestJS, quiser criar APIs REST ou GraphQL com Node.js, precisar de estrutura de projeto backend com TypeScript, trabalhar com módulos, controllers, services, guards, interceptors, DTOs, pipes, filters, autenticação JWT, banco de dados com TypeORM ou Prisma, testes com Jest, Swagger/OpenAPI, filas com Bull, WebSockets, ou qualquer padrão arquitetural do NestJS. Também ative para dúvidas sobre boas práticas, performance, segurança e organização de código NestJS.
---

# NestJS Development Skill

NestJS é um framework Node.js progressivo e opinativo, construído com TypeScript, que abraça os padrões de injeção de dependência, arquitetura modular e decorators inspirados no Angular.

---

## Filosofia e Princípios

- **Módulos** isolam contextos de domínio — cada feature tem seu próprio módulo
- **Injeção de Dependência** é automática via `@Injectable()` e o container IoC
- **Decorators** configuram comportamento de forma declarativa
- **Camadas** separadas: Controller (HTTP) → Service (lógica) → Repository (dados)
- Prefira `async/await` a callbacks; exponha apenas o que for necessário

---

## Estrutura de Projeto Recomendada

```
src/
├── common/               # Shared: guards, interceptors, filters, decorators, DTOs
│   ├── decorators/
│   ├── filters/
│   ├── guards/
│   ├── interceptors/
│   └── pipes/
├── config/               # Configuração por ambiente
├── modules/
│   └── users/            # Exemplo de módulo de domínio
│       ├── dto/
│       │   ├── create-user.dto.ts
│       │   └── update-user.dto.ts
│       ├── entities/
│       │   └── user.entity.ts
│       ├── users.controller.ts
│       ├── users.service.ts
│       ├── users.module.ts
│       └── users.repository.ts  (opcional)
├── app.module.ts
└── main.ts
```

---

## Módulo

```typescript
// users.module.ts
@Module({
  imports: [TypeOrmModule.forFeature([User])],
  controllers: [UsersController],
  providers: [UsersService],
  exports: [UsersService],  // só exporte o que outros módulos precisam
})
export class UsersModule {}
```

---

## Controller

```typescript
@Controller('users')
@UseGuards(JwtAuthGuard)
@ApiTags('Users')
export class UsersController {
  constructor(private readonly usersService: UsersService) {}

  @Post()
  @HttpCode(HttpStatus.CREATED)
  @ApiOperation({ summary: 'Criar usuário' })
  create(@Body() dto: CreateUserDto) {
    return this.usersService.create(dto);
  }

  @Get(':id')
  @ApiParam({ name: 'id', type: 'string' })
  findOne(@Param('id', ParseUUIDPipe) id: string) {
    return this.usersService.findOne(id);
  }

  @Patch(':id')
  update(@Param('id', ParseUUIDPipe) id: string, @Body() dto: UpdateUserDto) {
    return this.usersService.update(id, dto);
  }

  @Delete(':id')
  @HttpCode(HttpStatus.NO_CONTENT)
  remove(@Param('id', ParseUUIDPipe) id: string) {
    return this.usersService.remove(id);
  }
}
```

---

## Service

```typescript
@Injectable()
export class UsersService {
  constructor(
    @InjectRepository(User)
    private readonly userRepository: Repository<User>,
  ) {}

  async create(dto: CreateUserDto): Promise<User> {
    const existing = await this.userRepository.findOneBy({ email: dto.email });
    if (existing) throw new ConflictException('E-mail já cadastrado');

    const user = this.userRepository.create({
      ...dto,
      password: await bcrypt.hash(dto.password, 10),
    });
    return this.userRepository.save(user);
  }

  async findOne(id: string): Promise<User> {
    const user = await this.userRepository.findOneBy({ id });
    if (!user) throw new NotFoundException(`Usuário ${id} não encontrado`);
    return user;
  }

  async update(id: string, dto: UpdateUserDto): Promise<User> {
    const user = await this.findOne(id);
    Object.assign(user, dto);
    return this.userRepository.save(user);
  }

  async remove(id: string): Promise<void> {
    const user = await this.findOne(id);
    await this.userRepository.remove(user);
  }
}
```

---

## DTOs com Validação

```typescript
// create-user.dto.ts
export class CreateUserDto {
  @ApiProperty({ example: 'João Silva' })
  @IsString()
  @IsNotEmpty()
  @MaxLength(100)
  name: string;

  @ApiProperty({ example: 'joao@email.com' })
  @IsEmail()
  email: string;

  @ApiProperty({ minLength: 8 })
  @IsString()
  @MinLength(8)
  @Matches(/^(?=.*[A-Z])(?=.*\d)/, {
    message: 'Senha precisa ter ao menos uma letra maiúscula e um número',
  })
  password: string;

  @ApiPropertyOptional()
  @IsOptional()
  @IsEnum(UserRole)
  role?: UserRole;
}

// update usa PartialType para tornar todos os campos opcionais
export class UpdateUserDto extends PartialType(
  OmitType(CreateUserDto, ['email'] as const),
) {}
```

---

## Entidade (TypeORM)

```typescript
@Entity('users')
export class User {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ length: 100 })
  name: string;

  @Column({ unique: true })
  email: string;

  @Column({ select: false })  // nunca retorna o hash por padrão
  password: string;

  @Column({ type: 'enum', enum: UserRole, default: UserRole.USER })
  role: UserRole;

  @Column({ default: true })
  isActive: boolean;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;

  @DeleteDateColumn()        // soft delete
  deletedAt?: Date;
}
```

---

## main.ts — Bootstrap

```typescript
async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  // Prefix global de API
  app.setGlobalPrefix('api/v1');

  // Validação global
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,           // remove campos não declarados no DTO
      forbidNonWhitelisted: true,
      transform: true,           // converte tipos automaticamente
      transformOptions: { enableImplicitConversion: true },
    }),
  );

  // Filtro global de erros
  app.useGlobalFilters(new AllExceptionsFilter());

  // Interceptor global de serialização
  app.useGlobalInterceptors(new ClassSerializerInterceptor(app.get(Reflector)));

  // CORS
  app.enableCors({
    origin: process.env.ALLOWED_ORIGINS?.split(',') ?? '*',
    methods: ['GET', 'POST', 'PATCH', 'DELETE'],
    credentials: true,
  });

  // Swagger
  const config = new DocumentBuilder()
    .setTitle('API')
    .setVersion('1.0')
    .addBearerAuth()
    .build();
  SwaggerModule.setup('docs', app, SwaggerModule.createDocument(app, config));

  // Helmet (segurança de headers)
  app.use(helmet());

  await app.listen(process.env.PORT ?? 3000);
}
bootstrap();
```

---

## Referências Especializadas

Para tópicos avançados, consulte os arquivos de referência:

| Tópico | Arquivo | Quando Usar |
|---|---|---|
| Autenticação JWT + Passport | `references/auth.md` | Login, guards, refresh tokens |
| Banco de Dados | `references/database.md` | TypeORM, Prisma, migrations, transactions |
| Padrões Avançados | `references/patterns.md` | Guards, interceptors, pipes, filters, eventos |
| Testes | `references/testing.md` | Unit, integration, e2e com Jest |

---

## Checklist de Qualidade

Antes de considerar um módulo pronto, verifique:

- [ ] DTOs validados com `class-validator` + `whitelist: true`
- [ ] Erros mapeados para exceções HTTP do NestJS (`NotFoundException`, `ConflictException`, etc.)
- [ ] Entidades sem campos sensíveis expostos (use `@Exclude()` ou `select: false`)
- [ ] Rotas protegidas por Guards quando necessário
- [ ] Swagger documentado (`@ApiTags`, `@ApiOperation`, `@ApiResponse`)
- [ ] Testes unitários do Service e de integração do Controller
- [ ] Variáveis de ambiente validadas com `@nestjs/config` + Joi
- [ ] Índices de banco definidos nas Entities críticas