# Testes NestJS — Jest

## Estrutura e Configuração

```bash
# Já incluído no NestJS
# Rodar testes
npm test                  # unit
npm run test:watch        # watch mode
npm run test:cov          # cobertura
npm run test:e2e          # end-to-end
```

```jsonc
// jest.config.ts
export default {
  moduleFileExtensions: ['js', 'json', 'ts'],
  rootDir: 'src',
  testRegex: '.*\\.spec\\.ts$',
  transform: { '^.+\\.(t|j)s$': 'ts-jest' },
  collectCoverageFrom: ['**/*.(t|j)s', '!**/*.module.(t|j)s', '!**/main.ts'],
  coverageDirectory: '../coverage',
  testEnvironment: 'node',
};
```

---

## Teste Unitário — Service

```typescript
// users.service.spec.ts
describe('UsersService', () => {
  let service: UsersService;
  let userRepository: jest.Mocked<Repository<User>>;

  beforeEach(async () => {
    const module = await Test.createTestingModule({
      providers: [
        UsersService,
        {
          provide: getRepositoryToken(User),
          useValue: {
            findOneBy: jest.fn(),
            create: jest.fn(),
            save: jest.fn(),
            remove: jest.fn(),
          },
        },
      ],
    }).compile();

    service = module.get(UsersService);
    userRepository = module.get(getRepositoryToken(User));
  });

  describe('findOne', () => {
    it('deve retornar o usuário quando encontrado', async () => {
      const user = { id: '1', name: 'Test', email: 'test@test.com' } as User;
      userRepository.findOneBy.mockResolvedValue(user);

      const result = await service.findOne('1');

      expect(result).toEqual(user);
      expect(userRepository.findOneBy).toHaveBeenCalledWith({ id: '1' });
    });

    it('deve lançar NotFoundException quando não encontrado', async () => {
      userRepository.findOneBy.mockResolvedValue(null);

      await expect(service.findOne('999')).rejects.toThrow(NotFoundException);
    });
  });

  describe('create', () => {
    it('deve criar usuário com senha hasheada', async () => {
      const dto = { name: 'Test', email: 'test@test.com', password: 'Senha123' };
      const savedUser = { id: '1', ...dto, password: 'hashedPassword' } as User;

      userRepository.findOneBy.mockResolvedValue(null);
      userRepository.create.mockReturnValue(savedUser);
      userRepository.save.mockResolvedValue(savedUser);

      const result = await service.create(dto);

      expect(result).toEqual(savedUser);
      expect(userRepository.findOneBy).toHaveBeenCalledWith({ email: dto.email });
    });

    it('deve lançar ConflictException se email já existe', async () => {
      const dto = { name: 'Test', email: 'test@test.com', password: 'Senha123' };
      userRepository.findOneBy.mockResolvedValue({ id: '1' } as User);

      await expect(service.create(dto)).rejects.toThrow(ConflictException);
    });
  });
});
```

---

## Teste Unitário — Controller

```typescript
// users.controller.spec.ts
describe('UsersController', () => {
  let controller: UsersController;
  let service: jest.Mocked<UsersService>;

  beforeEach(async () => {
    const module = await Test.createTestingModule({
      controllers: [UsersController],
      providers: [
        {
          provide: UsersService,
          useValue: {
            create: jest.fn(),
            findOne: jest.fn(),
            update: jest.fn(),
            remove: jest.fn(),
          },
        },
      ],
    }).compile();

    controller = module.get(UsersController);
    service = module.get(UsersService);
  });

  it('deve chamar service.create com o DTO correto', async () => {
    const dto = { name: 'Test', email: 'test@test.com', password: 'Senha123' };
    const expected = { id: '1', ...dto } as User;
    service.create.mockResolvedValue(expected);

    const result = await controller.create(dto);

    expect(result).toEqual(expected);
    expect(service.create).toHaveBeenCalledWith(dto);
  });
});
```

---

## Teste de Integração — Repository

```typescript
// users.repository.spec.ts
describe('UsersRepository (integration)', () => {
  let dataSource: DataSource;
  let repo: Repository<User>;

  beforeAll(async () => {
    dataSource = await new DataSource({
      type: 'sqlite',           // SQLite em memória para testes
      database: ':memory:',
      entities: [User],
      synchronize: true,
    }).initialize();
    repo = dataSource.getRepository(User);
  });

  afterAll(() => dataSource.destroy());
  afterEach(() => repo.clear());

  it('deve salvar e buscar usuário', async () => {
    const user = repo.create({
      name: 'Test',
      email: 'test@test.com',
      password: 'hashed',
    });
    const saved = await repo.save(user);

    const found = await repo.findOneBy({ id: saved.id });
    expect(found).toMatchObject({ name: 'Test', email: 'test@test.com' });
  });
});
```

---

## Teste E2E

```typescript
// test/users.e2e-spec.ts
describe('UsersController (e2e)', () => {
  let app: INestApplication;
  let accessToken: string;
  let createdUserId: string;

  beforeAll(async () => {
    const moduleFixture = await Test.createTestingModule({
      imports: [AppModule],
    })
      .overrideProvider(ConfigService)
      .useValue(mockConfigService)
      .compile();

    app = moduleFixture.createNestApplication();
    app.useGlobalPipes(new ValidationPipe({ whitelist: true }));
    app.useGlobalFilters(new AllExceptionsFilter());
    await app.init();
  });

  afterAll(() => app.close());

  describe('POST /api/v1/auth/login', () => {
    it('deve retornar tokens para credenciais válidas', () => {
      return request(app.getHttpServer())
        .post('/api/v1/auth/login')
        .send({ email: 'admin@test.com', password: 'Admin123' })
        .expect(200)
        .expect((res) => {
          expect(res.body).toHaveProperty('accessToken');
          accessToken = res.body.accessToken;
        });
    });

    it('deve retornar 401 para credenciais inválidas', () => {
      return request(app.getHttpServer())
        .post('/api/v1/auth/login')
        .send({ email: 'admin@test.com', password: 'errado' })
        .expect(401);
    });
  });

  describe('POST /api/v1/users', () => {
    it('deve criar um usuário', () => {
      return request(app.getHttpServer())
        .post('/api/v1/users')
        .set('Authorization', `Bearer ${accessToken}`)
        .send({
          name: 'Novo Usuário',
          email: 'novo@test.com',
          password: 'Senha123',
        })
        .expect(201)
        .expect((res) => {
          expect(res.body).toHaveProperty('id');
          expect(res.body).not.toHaveProperty('password');
          createdUserId = res.body.id;
        });
    });

    it('deve retornar 400 para DTO inválido', () => {
      return request(app.getHttpServer())
        .post('/api/v1/users')
        .set('Authorization', `Bearer ${accessToken}`)
        .send({ name: 'Sem email' })
        .expect(400);
    });
  });

  describe('GET /api/v1/users/:id', () => {
    it('deve retornar o usuário criado', () => {
      return request(app.getHttpServer())
        .get(`/api/v1/users/${createdUserId}`)
        .set('Authorization', `Bearer ${accessToken}`)
        .expect(200)
        .expect((res) => {
          expect(res.body.id).toBe(createdUserId);
        });
    });
  });
});
```

---

## Helpers de Teste

```typescript
// test/helpers/auth.helper.ts
export async function getAuthToken(app: INestApplication, role = UserRole.ADMIN) {
  const res = await request(app.getHttpServer())
    .post('/api/v1/auth/login')
    .send({ email: `${role.toLowerCase()}@test.com`, password: 'Test1234' });
  return res.body.accessToken as string;
}

// test/helpers/database.helper.ts
export async function clearDatabase(dataSource: DataSource) {
  const entities = dataSource.entityMetadatas;
  for (const entity of entities) {
    await dataSource.getRepository(entity.name).clear();
  }
}
```

---

## Boas Práticas de Teste

- **Unitário** (`.spec.ts`): mock todos os deps externos; teste cada método do service isoladamente
- **E2E** (`test/*.e2e-spec.ts`): banco em memória (SQLite) ou container Docker; não mocke o banco em e2e
- **Cobertura**: mire em 80%+ nos services; controllers costumam ser mais simples
- Use `describe/it` descritivos: `"deve lançar NotFoundException quando usuário não existe"`
- **Arrange / Act / Assert** — separe visualmente as três fases
- Limpe o banco `afterEach` em testes de integração para isolar os casos
- Prefira `toMatchObject` a `toEqual` quando comparar subsets do objeto