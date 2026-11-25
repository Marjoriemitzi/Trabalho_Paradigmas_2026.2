# Códigos de erro e de aviso da API

O frontend decide o que mostrar pelo campo `error` das respostas e pelos `warnings` do lançamento.
Todo erro tem o formato `{"error": "<codigo>"}`, às vezes com `fields` (lista de `{field, problem}`)
ou `reasons`.

Regras para quem acrescenta um código:

- O código é sempre uma **string literal** no código-fonte (`error_response(status, "codigo")`,
  `ApiError(status, "codigo")`, `TransactionWarning("codigo")`). Código montado em tempo de execução
  é proibido. A única exceção é `_code_for_status` em `error_handlers.py`, que deriva o código do
  status HTTP.
- O mesmo PR que cria o código acrescenta a linha neste documento. O teste
  `Backend/tests/test_api_codes.py` falha se faltar.
- A primeira coluna das tabelas é o código, entre crases.

## Erros

| Código | Status | Quando acontece | Extras | Rotas |
| --- | --- | --- | --- | --- |
| `invalid_request` | 422 | Pedido fora da forma: campo faltando ou a mais, tipo errado, JSON inválido, id que não é UUID, data mal formada. | `fields: [{field, problem}]`; `problem` é o tipo do Pydantic (`missing`, `extra_forbidden`, `uuid_parsing`, `json_invalid`…); `field` é `null` quando o JSON é inválido. | todas |
| `internal_error` | 500 | Erro inesperado no servidor. | — | todas |
| `not_found` | 404 | Rota que não existe (derivado do status). | — | qualquer caminho |
| `method_not_allowed` | 405 | Método HTTP que a rota não aceita (derivado do status). | — | todas |
| `not_authenticated` | 401 | Pedido sem token, ou com outro esquema de autenticação. | `WWW-Authenticate: Bearer` | rotas protegidas |
| `invalid_token` | 401 | Token inválido, vencido, revogado, ou de usuário que não existe mais. | `WWW-Authenticate: Bearer error="invalid_token"` | rotas protegidas |
| `invalid_credentials` | 401 | E-mail ou senha incorretos. | `WWW-Authenticate: Bearer` | `POST /api/v1/auth/login` |
| `invalid_refresh_token` | 401 | Refresh token desconhecido, vencido, revogado ou já usado (o reuso revoga a sessão). | — | `POST /api/v1/auth/refresh` |
| `too_many_attempts` | 429 | Falhas de login ou cadastros demais no período. | cabeçalho `Retry-After` (segundos) | `POST /api/v1/auth/login`, `POST /api/v1/users` |
| `email_taken` | 409 | E-mail já cadastrado. | — | `POST /api/v1/users` |
| `invalid_email` | 422 | E-mail mal formado. | — | `POST /api/v1/users` |
| `weak_password` | 422 | Senha nova não passa na política (`rules/users/password_policy.pl`) ou contém byte NUL. | `reasons: [too_short, no_upper, no_lower, no_digit, no_symbol, invalid_character]` (aqui é `reasons`, não `fields`) | `POST /api/v1/users`, `POST /api/v1/users/me/password` |
| `invalid_current_password` | 422 | Senha atual errada ao trocar a senha ou apagar a conta. | — | `POST /api/v1/users/me/password`, `DELETE /api/v1/users/me` |
| `invalid_account` | 422 | Dado da conta recusado. | `fields`: `name` (`blank`, `too_long`), `kind` (`unknown`) | `POST /api/v1/accounts`, `PATCH /api/v1/accounts/{id}` |
| `account_name_taken` | 409 | Já existe uma conta da pessoa com esse nome (sem diferenciar maiúsculas). | — | `POST /api/v1/accounts`, `PATCH /api/v1/accounts/{id}` |
| `account_in_use` | 409 | A conta tem transações ou transferências e não pode ser apagada. | — | `DELETE /api/v1/accounts/{id}` |
| `account_not_found` | 404 | A conta não existe entre as da pessoa (igual para "não existe" e "é de outra pessoa"). | — | extrato com `account_id`, `PATCH` e `DELETE` de conta |
| `invalid_transaction` | 422 | Dado do lançamento recusado. | `fields`: `kind` (`unknown`), `amount_cents` (`not_positive`, `too_large`), `description` (`blank`, `too_long`, `invalid_format`), `category` (`invalid_format`, `not_found`), `account_id` (`not_found`) | `POST` e `PUT /api/v1/transactions` |
| `transaction_not_found` | 404 | O lançamento não existe entre os da pessoa. | — | `PUT` e `DELETE /api/v1/transactions/{id}` |
| `invalid_period` | 422 | Período recusado. | `fields`: `to` (`end_before_start`, `too_long`) | `GET /api/v1/transactions`, `GET /api/v1/transfers` |
| `invalid_transfer` | 422 | Dado da transferência recusado. | `fields`: `amount_cents` (`not_positive`, `too_large`), `description` (`blank`, `too_long`, `invalid_format`), `from_account_id` e `to_account_id` (`not_found`), `to_account_id` (`same_account`) | `POST` e `PUT /api/v1/transfers` |
| `transfer_not_found` | 404 | A transferência não existe entre as da pessoa. | — | `PUT` e `DELETE /api/v1/transfers/{id}` |
| `invalid_recurrence` | 422 | Dado da recorrência recusado. | `fields`: `account_id` (`not_found`), `kind` (`unknown`), `amount_cents` (`not_positive`, `too_large`), `description` (`blank`, `too_long`, `invalid_format`), `category` (`invalid_format`, `not_found`), `frequency` (`unknown`), `day` (`out_of_range`), `ends_on` (`end_before_start`) | `POST` e `PUT /api/v1/recurrences` |
| `recurrence_not_found` | 404 | A recorrência não existe entre as da pessoa. | — | `PUT` e `DELETE /api/v1/recurrences/{id}` |

## Problemas de campo

Valores de `fields[].problem` que vêm do domínio.

| Problema | Significado |
| --- | --- |
| `blank` | O texto está vazio ou só com espaços. |
| `too_long` | Passou do tamanho máximo (nome da conta e descrições) ou do período máximo (366 dias). |
| `not_positive` | O valor em centavos precisa ser maior que zero. |
| `too_large` | O valor em centavos passou do teto aceito (`9999999999999`, cerca de R$ 100 bilhões). |
| `unknown` | Valor fora da lista aceita (tipo de conta ou de lançamento). |
| `invalid_format` | O texto (categoria ou descrição) não tem o formato aceito. |
| `not_found` | A referência (conta ou categoria) não existe para a pessoa. |
| `same_account` | A transferência tem a mesma conta na origem e no destino. |
| `end_before_start` | A data final é anterior à inicial. |
| `out_of_range` | O dia está fora da faixa da frequência (1 a 31 no mês, 1 a 7 na semana). |

## Avisos

Os `warnings` do lançamento (`TransactionWarning`) ainda não têm nenhum código: a tupla `checks` de
`app/wiring.py` está vazia. Cada aviso novo entra aqui, com as chaves de `details`.

| Código | Quando acontece | Chaves de `details` |
| --- | --- | --- |
