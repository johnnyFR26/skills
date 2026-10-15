---
name: solid-development
description: Guia de desenvolvimento orientado pelos princípios SOLID (SRP, OCP, LSP, ISP, DIP). Use SEMPRE que for escrever, revisar, refatorar ou projetar código orientado a objetos ou modular — classes, serviços, módulos, APIs, handlers, casos de uso — mesmo que o usuário não mencione "SOLID". Acione também quando surgirem termos como "refatorar", "code smell", "acoplamento", "coesão", "injeção de dependência", "clean code", "arquitetura limpa", "classe muito grande", "difícil de testar" ou "if/switch gigante".
---

# Desenvolvimento SOLID

Siga este guia ao criar ou alterar código. O objetivo é código coeso, extensível e testável, sem over-engineering.

## Fluxo de trabalho

1. **Entenda a responsabilidade.** Antes de codar, descreva em uma frase o que a unidade (classe/módulo/função) faz. Se precisar de "e" ou "ou", provavelmente são duas responsabilidades.
2. **Identifique os eixos de mudança.** Pergunte: o que muda com frequência (regras de negócio, provedores externos, formatos, canais)? Isole isso atrás de abstrações.
3. **Defina contratos pequenos.** Crie interfaces enxutas, orientadas ao consumidor.
4. **Injete dependências.** Receba colaboradores pelo construtor; componha tudo em um único ponto (composition root).
5. **Verifique com o checklist** no final antes de entregar.
6. **Explique as decisões.** Ao entregar, cite em 1–3 linhas quais princípios guiaram a estrutura e o que foi propositalmente mantido simples.

## Os cinco princípios

### S — Single Responsibility (Responsabilidade Única)
Uma unidade deve ter um único motivo para mudar.

- **Sinais de violação:** classe com nome genérico (`Manager`, `Helper`, `Utils`), mistura de regra de negócio com I/O, banco, HTTP, formatação ou logging; muitos imports de camadas diferentes; testes que exigem muitos mocks.
- **Como corrigir:** separe por motivo de mudança (validação, persistência, notificação, cálculo). Extraia classes/funções com nomes que descrevem uma ação.

### O — Open/Closed (Aberto/Fechado)
Aberto para extensão, fechado para modificação.

- **Sinais de violação:** `if/else` ou `switch` por tipo que cresce a cada novo caso; alterar código existente para adicionar variação.
- **Como corrigir:** extraia uma abstração (interface/estratégia) e uma implementação por variação; selecione a implementação via registro, mapa ou injeção. Adicionar um caso = criar uma classe nova, não editar as antigas.

### L — Liskov Substitution (Substituição de Liskov)
Subtipos devem poder substituir seus tipos base sem quebrar o comportamento esperado.

- **Sinais de violação:** subclasse que lança `NotImplemented`/exceção inesperada, enfraquece pré-condições, fortalece pós-condições, ignora parâmetros ou exige checagem de tipo (`instanceof`) no chamador.
- **Como corrigir:** prefira composição à herança; redesenhe a hierarquia (ex.: `Bird` → `FlyingBird`); respeite o contrato (entradas, saídas, erros, invariantes) da abstração.

### I — Interface Segregation (Segregação de Interfaces)
Clientes não devem depender de métodos que não usam.

- **Sinais de violação:** interface "gorda" com métodos que implementações deixam vazios; mudança em um método afeta implementadores que não o usam.
- **Como corrigir:** divida em interfaces pequenas por papel (`Reader`, `Writer`, `Notifier`); o consumidor define o que precisa.

### D — Dependency Inversion (Inversão de Dependência)
Módulos de alto nível dependem de abstrações, não de detalhes concretos.

- **Sinais de violação:** `new ConcreteService()` dentro da regra de negócio; import direto de driver/SDK/ORM no domínio; impossibilidade de testar sem infraestrutura real.
- **Como corrigir:** declare a interface no lado do domínio/caso de uso (port), implemente na infraestrutura (adapter) e injete pelo construtor.

## Exemplo rápido (TypeScript)

**Antes** — viola S, O e D:

```ts
class OrderService {
  create(order: Order, channel: string) {
    if (!order.items.length) throw new Error("Pedido vazio");
    db.insert("orders", order); // detalhe concreto
    if (channel === "email") sendgrid.send(order.customer.email, "Ok");
    else if (channel === "sms") twilio.send(order.customer.phone, "Ok");
  }
}
```

**Depois:**

```ts
interface OrderRepository { save(order: Order): Promise<void>; }
interface Notifier { notify(customer: Customer, msg: string): Promise<void>; }

class CreateOrder {
  constructor(
    private readonly repo: OrderRepository,
    private readonly notifier: Notifier,
  ) {}

  async execute(order: Order): Promise<void> {
    if (!order.items.length) throw new EmptyOrderError();
    await this.repo.save(order);
    await this.notifier.notify(order.customer, "Pedido criado");
  }
}

class EmailNotifier implements Notifier { /* ... */ }
class SmsNotifier implements Notifier { /* ... */ }
```

Novo canal (ex.: WhatsApp) = nova classe `WhatsAppNotifier`; `CreateOrder` não muda. Nos testes, use fakes simples de `OrderRepository` e `Notifier`.

## Pragmatismo (evite over-engineering)

SOLID é meio, não fim. Aplique com julgamento:

- **Não crie interface para algo que tem uma única implementação e nenhum motivo plausível de variar** (ex.: utilitário puro, DTO). Extraia a abstração quando surgir a segunda variação ou a necessidade de isolar I/O.
- **Regra dos três:** tolere duplicação até a terceira ocorrência, depois abstraia.
- **Funções puras e pequenas** também satisfazem SRP; em linguagens funcionais, "interface" pode ser uma função passada por parâmetro.
- **Respeite as convenções do projeto** (estrutura de pastas, nomes, framework). Refatore de forma incremental, com testes protegendo o comportamento.
- Em scripts, protótipos e código descartável, priorize simplicidade e avise que a estrutura SOLID foi omitida de propósito.

## Checklist antes de entregar

- [ ] Cada classe/módulo tem uma responsabilidade descrita em uma frase?
- [ ] Adicionar uma variação nova evita editar código existente?
- [ ] Todo subtipo funciona onde o tipo base é esperado, sem checagem de tipo?
- [ ] Nenhum implementador precisa deixar métodos vazios ou lançar "não suportado"?
- [ ] Regras de negócio dependem de abstrações, e não de banco/HTTP/SDK?
- [ ] Dependências são injetadas e a composição fica em um único lugar?
- [ ] A unidade é testável com fakes simples, sem infraestrutura real?
- [ ] A abstração criada se justifica (não é complexidade especulativa)?

## Revisão de código existente

Ao revisar ou refatorar código de terceiros:

1. Liste as violações encontradas, agrupadas por princípio, apontando arquivo/linha e o sintoma concreto.
2. Priorize por impacto (acoplamento à infraestrutura e `switch` por tipo costumam trazer o maior retorno).
3. Proponha refatorações em passos pequenos e seguros, começando por escrever ou confirmar testes.
4. Mostre o código "antes/depois" apenas dos trechos relevantes.

Para mais exemplos por princípio e anti-padrões comuns, consulte `references/exemplos.md`.
