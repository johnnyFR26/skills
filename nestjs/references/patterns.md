# Padrões Avançados NestJS

## Filtro Global de Exceções

```typescript
// all-exceptions.filter.ts
@Catch()
export class AllExceptionsFilter implements ExceptionFilter {
  private readonly logger = new Logger(AllExceptionsFilter.name);

  catch(exception: unknown, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();

    let status = HttpStatus.INTERNAL_SERVER_ERROR;
    let message: string | string[] = 'Erro interno do servidor';
    let error = 'Internal Server Error';

    if (exception instanceof HttpException) {
      status = exception.getStatus();
      const res = exception.getResponse();
      message = typeof res === 'string' ? res : (res as any).message;
      error = (res as any).error ?? exception.message;
    } else if (exception instanceof QueryFailedError) {
      // Violação de unique constraint
      if ((exception as any).code === '23505') {
        status = HttpStatus.CONFLICT;
        message = 'Registro já existe';
        error = 'Conflict';
      }
    }

    if (status >= 500) {
      this.logger.error({ exception, request: request.url });
    }

    response.status(status).json({
      statusCode: status,
      error,
      message,
      path: request.url,
      timestamp: new Date().toISOString(),
    });
  }
}
```

---

## Interceptors

### Logging de Requests

```typescript
@Injectable()
export class LoggingInterceptor implements NestInterceptor {
  private readonly logger = new Logger('HTTP');

  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const req = context.switchToHttp().getRequest();
    const { method, url, body } = req;
    const now = Date.now();

    return next.handle().pipe(
      tap(() => {
        this.logger.log(`${method} ${url} ${Date.now() - now}ms`);
      }),
      catchError((err) => {
        this.logger.error(`${method} ${url} ${err.message}`);
        return throwError(() => err);
      }),
    );
  }
}
```

### Serialização e Exclusão de Campos

```typescript
// Na entidade
@Entity()
export class User {
  @Column({ select: false })
  @Exclude()  // nunca retorna na resposta HTTP
  password: string;

  @Expose({ groups: ['admin'] })
  internalNotes?: string;
}

// No controller
@UseInterceptors(ClassSerializerInterceptor)
@SerializeOptions({ excludeExtraneousValues: true })
findOne() { ... }
```

### Transform Response (envelope padrão)

```typescript
@Injectable()
export class TransformInterceptor<T> implements NestInterceptor<T, Response<T>> {
  intercept(context: ExecutionContext, next: CallHandler): Observable<Response<T>> {
    return next.handle().pipe(
      map((data) => ({
        success: true,
        data,
        timestamp: new Date().toISOString(),
      })),
    );
  }
}
```

---

## Pipes

### Pipe de Parse para Enum

```typescript
@Injectable()
export class ParseEnumPipe<T extends object> implements PipeTransform {
  constructor(private readonly enumType: T) {}

  transform(value: string) {
    if (!Object.values(this.enumType).includes(value)) {
      throw new BadRequestException(
        `${value} não é um valor válido. Aceitos: ${Object.values(this.enumType).join(', ')}`,
      );
    }
    return value;
  }
}

// Uso
@Get()
findByRole(@Query('role', new ParseEnumPipe(UserRole)) role: UserRole) {}
```

---

## Guards

### Rate Limiting Customizado

```typescript
// Instale: npm i @nestjs/throttler
ThrottlerModule.forRoot([{ ttl: 60000, limit: 10 }])

// Nos controllers
@UseGuards(ThrottlerGuard)
@Throttle({ default: { limit: 5, ttl: 60000 } })
@Post('login')
login() {}
```

### Permission Guard

```typescript
@Injectable()
export class PermissionGuard implements CanActivate {
  constructor(private reflector: Reflector) {}

  canActivate(context: ExecutionContext): boolean {
    const permissions = this.reflector.getAllAndOverride<Permission[]>(
      PERMISSIONS_KEY,
      [context.getHandler(), context.getClass()],
    );
    if (!permissions?.length) return true;

    const { user } = context.switchToHttp().getRequest<AuthRequest>();
    return permissions.every((p) => user.permissions?.includes(p));
  }
}
```

---

## Configuração com Validação (Joi)

```typescript
// config/app.config.ts
export const appConfig = registerAs('app', () => ({
  port: parseInt(process.env.PORT, 10) || 3000,
  jwtSecret: process.env.JWT_SECRET,
  nodeEnv: process.env.NODE_ENV || 'development',
  databaseUrl: process.env.DATABASE_URL,
}));

// app.module.ts
ConfigModule.forRoot({
  isGlobal: true,
  load: [appConfig],
  validationSchema: Joi.object({
    NODE_ENV: Joi.string().valid('development', 'production', 'test').required(),
    PORT: Joi.number().default(3000),
    DATABASE_URL: Joi.string().uri().required(),
    JWT_SECRET: Joi.string().min(32).required(),
  }),
  validationOptions: { abortEarly: false },
}),

// Uso no service
constructor(@Inject(appConfig.KEY) private config: ConfigType<typeof appConfig>) {}
// this.config.port, this.config.jwtSecret...
```

---

## Eventos (EventEmitter)

```typescript
npm i @nestjs/event-emitter

// app.module.ts
EventEmitterModule.forRoot()

// Emitir evento
constructor(private eventEmitter: EventEmitter2) {}
this.eventEmitter.emit('order.created', new OrderCreatedEvent(order));

// Ouvir evento
@OnEvent('order.created', { async: true })
async handleOrderCreated(event: OrderCreatedEvent) {
  await this.notificationService.sendConfirmation(event.order);
}
```

---

## Cache

```typescript
npm i @nestjs/cache-manager cache-manager

// app.module.ts
CacheModule.registerAsync({
  isGlobal: true,
  imports: [ConfigModule],
  inject: [ConfigService],
  useFactory: async (config: ConfigService) => ({
    ttl: 60, // segundos
    max: 100,
    // Redis:
    // store: require('cache-manager-redis-store'),
    // url: config.get('REDIS_URL'),
  }),
})

// No controller/service
@UseInterceptors(CacheInterceptor)
@CacheTTL(30)
@Get('products')
findAll() { ... }

// Manual
constructor(@Inject(CACHE_MANAGER) private cacheManager: Cache) {}

const cached = await this.cacheManager.get<Product[]>('products');
await this.cacheManager.set('products', data, 60);
await this.cacheManager.del('products');
```

---

## WebSockets

```typescript
npm i @nestjs/websockets @nestjs/platform-socket.io socket.io

@WebSocketGateway({ cors: { origin: '*' }, namespace: '/events' })
export class EventsGateway implements OnGatewayConnection, OnGatewayDisconnect {
  @WebSocketServer() server: Server;

  handleConnection(client: Socket) {
    console.log(`Client connected: ${client.id}`);
  }

  handleDisconnect(client: Socket) {
    console.log(`Client disconnected: ${client.id}`);
  }

  @SubscribeMessage('message')
  handleMessage(client: Socket, payload: { room: string; content: string }) {
    this.server.to(payload.room).emit('message', payload);
  }

  // Emitir para todos os clientes (de qualquer service)
  broadcastToRoom(room: string, event: string, data: any) {
    this.server.to(room).emit(event, data);
  }
}
```

---

## Filas com Bull

```typescript
npm i @nestjs/bull bull
npm i -D @types/bull

// app.module.ts
BullModule.forRoot({ redis: { host: 'localhost', port: 6379 } })

// email.module.ts
BullModule.registerQueue({ name: 'email' })

// Producer
constructor(@InjectQueue('email') private emailQueue: Queue) {}
await this.emailQueue.add('welcome', { to: user.email }, { attempts: 3, backoff: 5000 });

// Consumer
@Processor('email')
export class EmailProcessor {
  @Process('welcome')
  async handleWelcome(job: Job<{ to: string }>) {
    await this.mailerService.sendWelcome(job.data.to);
  }

  @OnQueueFailed()
  onFailed(job: Job, err: Error) {
    console.error(`Job ${job.id} failed: ${err.message}`);
  }
}
```

---

## Health Check

```typescript
npm i @nestjs/terminus

@Controller('health')
@ApiTags('Health')
export class HealthController {
  constructor(
    private health: HealthCheckService,
    private db: TypeOrmHealthIndicator,
    private memory: MemoryHealthIndicator,
  ) {}

  @Get()
  @Public()
  @HealthCheck()
  check() {
    return this.health.check([
      () => this.db.pingCheck('database'),
      () => this.memory.checkHeap('memory_heap', 150 * 1024 * 1024),
    ]);
  }
}
```