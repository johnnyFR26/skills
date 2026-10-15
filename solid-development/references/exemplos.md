# Exemplos e anti-padrões por princípio

## SRP
**Anti-padrão:** `UserService` que valida, grava no banco, envia e-mail de boas-vindas e gera relatório.
**Refatoração:** `UserValidator`, `UserRepository`, `WelcomeEmailSender`, `UserReportGenerator`, orquestrados por um caso de uso `RegisterUser`.

## OCP
**Anti-padrão:**
```ts
function discount(type: string, total: number) {
  switch (type) {
    case "regular": return total;
    case "vip": return total * 0.9;
    case "black": return total * 0.8;
  }
}
```
**Refatoração:**
```ts
interface DiscountPolicy { apply(total: number): number; }
class VipDiscount implements DiscountPolicy { apply(t: number) { return t * 0.9; } }
class BlackDiscount implements DiscountPolicy { apply(t: number) { return t * 0.8; } }

const policies: Record<string, DiscountPolicy> = {
  vip: new VipDiscount(),
  black: new BlackDiscount(),
};
```

## LSP
**Anti-padrão:** `Square extends Rectangle` alterando `setWidth` para também mudar a altura, quebrando quem espera independência entre os lados.
**Refatoração:** abstração `Shape { area(): number }` com `Rectangle` e `Square` independentes.

**Anti-padrão:** `ReadOnlyRepository extends Repository` lançando erro em `save()`.
**Refatoração:** separar `ReadRepository` e `WriteRepository`.

## ISP
**Anti-padrão:**
```ts
interface Worker { work(): void; eat(): void; }
class Robot implements Worker { work() {} eat() { throw new Error("N/A"); } }
```
**Refatoração:** `Workable { work() }` e `Feedable { eat() }`.

## DIP
**Anti-padrão:** caso de uso importando `PrismaClient` ou `axios` diretamente.
**Refatoração:** o caso de uso depende de `OrderRepository` / `PaymentGateway` (interfaces no domínio); `PrismaOrderRepository` e `StripePaymentGateway` vivem na infraestrutura e são ligados no composition root.

```ts
// composition root
const repo = new PrismaOrderRepository(prisma);
const notifier = new EmailNotifier(mailer);
const createOrder = new CreateOrder(repo, notifier);
```

## Smells que indicam violação
| Smell | Princípio provável |
|---|---|
| Classe com mais de ~300 linhas ou muitos métodos não relacionados | SRP |
| `switch`/`if-else` por tipo repetido em vários lugares | OCP |
| `instanceof` no chamador, `throw NotSupported` em override | LSP |
| Métodos vazios em implementações | ISP |
| `new` de serviços concretos dentro da regra de negócio | DIP |
| Testes exigindo banco, rede ou muitos mocks | SRP / DIP |
