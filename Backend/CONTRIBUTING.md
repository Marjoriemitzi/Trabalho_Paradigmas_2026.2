# Como criar uma feature no backend

Este guia leva uma feature nova do zero até um PR pronto, na ordem em que o projeto trabalha.
O código segue Clean Architecture, DDD e TDD. Todos os comandos rodam **dentro do Docker**, na
raiz do monorepo (veja o [README do backend](README.md)): nada de `poetry run` nem `pip install`
na sua máquina.

Os exemplos usam fatias que já existem. Abra-as ao lado deste guia:

- `create_account`: escrita com unicidade. Caminho completo, de dentro para fora:
  `domain/entities/account.py`, `domain/repositories/account_repository.py`,
  `infrastructure/persistence/repositories/sql_account_repository.py`,
  `application/use_cases/create_account.py`,
  `presentation/api/v1/presenters/create_account_presenter.py`,
  `presentation/api/v1/controllers/accounts_controllers.py` e
  `presentation/api/v1/routers/accounts.py` (todos em `src/app/finance/`).
- `get_statement`: leitura com período e conta opcional.
- `recurrences` (`create_recurrence.py` e companhia): uma feature inteira com regra em Prolog,
  migration e caso de uso de fundo (`run_due_recurrences.py`).
- `SpendingReader` (`application/ports/spending_reader.py`): porta de leitura própria.
- `TransactionCheck` (`application/ports/transaction_check.py`): verificação plugável do lançamento.

## 1. Ordem de trabalho (TDD: o teste vem primeiro em cada passo)

1. **Domínio**: value objects, entidade e exceções em `domain/`. Sem framework, sem banco.
2. **Porta e teste de contrato**: o `Protocol` do repositório (ou da porta) e o teste de contrato em
   `tests/<contexto>/contracts/*_contract.py`.
3. **Fake em memória e implementação SQL**: os dois passam no **mesmo** contrato. O fake roda em
   `tests/<contexto>/unit/fakes/test_fake_*.py` e o SQL em `tests/<contexto>/integration/test_sql_*.py`.
4. **Migration** (veja o item 3).
5. **Caso de uso**: input port, output port e interactor, testado com os fakes e com um *spy* de
   presenter (`tests/<contexto>/fakes/*_presenter_spy.py`).
6. **Presenter, controller e rota**: `presentation/api/v1/`. O caminho é
   router → controller → input port → interactor → output port → presenter.
7. **Composição**: a fábrica do caso de uso e o registro (item 2).
8. **Teste real**: `tests/<contexto>/e2e/*_real.py`, com o PostgreSQL de verdade (item 8).

Além deles, cada rota tem um teste com fakes (`*_endpoint.py`) e cada presenter tem um teste de
unidade.

## 2. Onde registrar uma feature nova

| O quê | Onde |
| --- | --- |
| Fábrica do caso de uso | `app/finance/composition.py` (ou `app/users/composition.py`) |
| `app.state.<nome>` | `app/wiring.py`: `install_finance` (ou `install_users`) |
| Rota | `app/main.py`: `app.include_router(...)` |
| Verificação de lançamento | a tupla `checks` em `build_infra` (`app/wiring.py`) |
| `get_<nome>_controller` | `presentation/api/v1/dependencies.py` do contexto |
| Porta da Unit of Work | `application/ports/unit_of_work.py` |
| Unit of Work SQL | `infrastructure/persistence/unit_of_work.py` |
| Unit of Work falsa | `tests/finance/fakes/fake_unit_of_work.py` (ou `tests/users/fakes/`) |
| Import do model novo | `migrations/env.py`: sem ele o `--autogenerate` não enxerga a tabela |

`app/wiring.py` é a única montagem de dependências concretas. A API (`main.py`) e os comandos de
linha (`seed_demo.py`, `run_due_recurrences.py`) usam as mesmas fábricas, então uma `check` nova
registrada ali vale nos dois lugares.

## 3. Migrations

```bash
docker compose run --rm tools alembic revision --autogenerate -m "descrição"
docker compose exec app alembic upgrade head
docker compose exec app alembic check          # sem diferença entre os models e o banco
```

- **Revise o arquivo gerado à mão**: CHECKs, índices funcionais e FKs compostas nem sempre saem
  certos. Confira o nome das restrições (o projeto usa a convenção de `shared/.../database.py`).
- Uma migration **nunca importa código da aplicação**.
- Toda migration tem `downgrade()` funcionando. Teste: `alembic downgrade -1` e depois
  `alembic upgrade head`.
- **Uma ponta só.** Se a `main` recebeu outra migration enquanto você trabalhava,
  `tests/test_migrations.py` acusa duas pontas. Atualize a branch, troque o `down_revision` da sua
  migration para a nova ponta e rode `alembic upgrade head` de novo. **Não** crie migration de
  merge: a branch ainda não foi integrada, então o histórico fica linear.

## 4. Prolog

- Um `.pl` por área, em `Backend/rules/<contexto>/`.
- Cada arquivo começa com `:- module(nome, [predicado/aridade]).` e `:- encoding(utf8).` e exporta
  só o que o Python chama.
- Os parâmetros de negócio (percentuais, limites) ficam como fatos no `.pl`.
- Dinheiro em **centavos inteiros**, nunca `float`.
- O Python só conversa pelo `PrologGateway` (`holds`, `values`), passando valores como argumentos
  (`str` ou `int`). **Nunca** monte uma query concatenando texto de usuário: `shell/1` executa
  comandos.
- O adapter fica em `infrastructure/prolog/` e implementa uma porta do domínio (veja
  `prolog_recurrence_rules.py`).
- Nomes de predicados exportados não podem repetir entre módulos (`tests/test_rules.py` acusa).

## 5. Códigos de erro

- Formato único `{"error": "<codigo>"}`, às vezes com `fields` (lista de `{field, problem}`).
- `invalid_<coisa>` (422, com `fields`) para regra de domínio.
- `<coisa>_not_found` (404), igual para "não existe" e "é de outra pessoa".
- `<coisa>_taken` (409) para nome ou chave única já usada.
- `invalid_request` (422) é do FastAPI, para pedido fora da forma.
- O código é sempre uma **string literal** no presenter. Código montado em tempo de execução é
  proibido.
- Todo código novo entra no catálogo [`docs/api-codes.md`](docs/api-codes.md) no mesmo PR.
  `tests/test_api_codes.py` falha se faltar.

## 6. Leituras novas

Crie uma **porta de leitura própria**, exposta na Unit of Work, como o `SpendingReader`. Não
aumente o `TransactionRepository` com consultas de relatório.

## 7. Segurança

- O dono vem sempre do token (`CurrentUser`), nunca do corpo do pedido.
- Os schemas de entrada usam `extra="forbid"`, e dinheiro chega como `StrictInt`.
- Respostas com dado financeiro pessoal levam `Cache-Control: no-store` (o middleware global já
  cobre `/api/v1/*`).
- Segredos em `SecretStr` ou `field(repr=False)`; nunca em log.
- IP do cliente é `request.client.host`; a aplicação nunca lê `X-Forwarded-For`.

## 8. Testes reais

Sempre com um usuário novo por teste (fixture `auth_headers`, que usa `real_client` e
`fresh_email`). Nunca dependa de dados de outro teste. Cada teste real tem um IP próprio, então o
limite de tentativas não junta os testes.

## 9. Tipagem e estilo

O projeto roda `mypy --strict` (com `explicit-override`, `truthy-bool` e outros códigos extras) e
`ruff` (incluindo `ANN`, `FBT`, `PLR`, `TCH`, `PT`, `ARG`). Na prática:

- Anote tudo. `Any`, `# type: ignore` e `cast` só como último recurso, com o motivo num comentário.
- `@dataclass(frozen=True, slots=True)` (entidades mutáveis do domínio: `eq=False, slots=True`).
- `@override` em todo método que implementa um `Protocol` ou sobrescreve uma base.
- Parâmetros somente leitura como `Sequence` ou `Mapping`; comparações explícitas (`is None`,
  `== ""`) no lugar de `if not x`.
- Imports absolutos a partir de `app.`; nada de `sys.path` nem `PYTHONPATH` na mão.

## 10. Antes de abrir o PR

```bash
git fetch && git merge origin/main               # atualize a branch
docker compose exec app task check               # ruff, mypy, pytest e pip-audit
docker compose exec app alembic check            # sem diferença de schema
docker compose run --rm --no-deps tools ruff format .
docker compose run --rm --no-deps tools task openapi   # mudou rota ou schema? regenere
```

Confira também que o CI (`.github/workflows/backend.yml`) ficou verde. Ele roda os mesmos
comandos, mais `alembic downgrade base` seguido de `upgrade head`.

## 11. Arquivos onde os PRs se encostam

Estes arquivos recebem linhas de quase toda feature, então PRs paralelos conflitam neles:
`app/wiring.py`, `app/main.py`, `composition.py`, `presentation/api/v1/dependencies.py`, a Unit of
Work (porta, SQL e fake) e `migrations/env.py`. Neles, os PRs só **acrescentam** linhas: ao
resolver o conflito, mantenha as duas versões e a ordem alfabética dos imports.
