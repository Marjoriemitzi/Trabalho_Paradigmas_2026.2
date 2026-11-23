# Frontend — Finanças pessoais

Interface em Elm com login, cadastro, consulta do usuário, renovação
de sessão, logout com revogação no backend e gerenciamento de
contas financeiras.

## Requisitos

- Docker e Docker Compose.
- Node.js e npm para executar os testes e as ferramentas locais.

## Executar a aplicação

Na primeira execução, crie e configure o `.env` na raiz do projeto
usando o `.env.example` como referência.

Na raiz do projeto:

```bash
docker compose up -d --build
docker compose exec app alembic upgrade head
```

Acesse: http://127.0.0.1:5173

Se a porta local `5432` estiver ocupada, altere o mapeamento do serviço
`db` no `docker-compose.yml` para `127.0.0.1:5433:5432`.

## Aplicar alterações no frontend

Salve os arquivos e execute na raiz:

```bash
docker compose up -d --build frontend
```

Depois, atualize o navegador com `Ctrl + F5`.

## Executar os testes

Dentro de `Frontend/`, instale as dependências na primeira execução:

```bash
npm ci
```

Execute a suíte:

```bash
bash test.sh
```

O script executa os testes Playwright em um container com os navegadores
necessários. Na primeira execução, o download da imagem pode demorar.

Os testes cobrem login, cadastro, consulta do usuário, restauração e
renovação da sessão, logout, limite de tentativas e gerenciamento
de contas financeiras. O backend e o banco podem ficar desligados
durante os testes com a API simulada.

## Formatar e verificar a compilação

Dentro de `Frontend/`:

```bash
npm run format
npm run build
```

## Requisições autenticadas em novas telas

Em Elm, use `Api.request` com um identificador de operação, o método,
o caminho relativo a `/api/v1` e o corpo JSON. As telas que precisam
da lista de contas podem reutilizar `Accounts.listRequest` e
`Accounts.listDecoder`. Use um identificador próprio por tela, por
exemplo, `Api.request (Accounts.listRequest "transfers.accounts")`.

O `Main.elm` já assina `Api.responses`. Encaminhe a resposta à tela
pelo `id` e decodifique `response.body` conforme o endpoint. O corpo
é `null` no sucesso com HTTP 204. Erros da API mantêm o status, o
código e o JSON original. Erros de rede e timeout usam status 0.

O `bootstrap.js` acrescenta o Bearer, coordena a renovação e armazena
o par de tokens em `sessionStorage`. Use identificadores próprios
para as telas. Os identificadores `login`, `registration`, `profile`
e `session-ended` pertencem ao fluxo de sessão.

## Encerrar a aplicação

Na raiz:

```bash
docker compose down
```

Os dados do banco são preservados.