# Frontend — Finanças pessoais

Interface em Elm com login, cadastro, consulta do usuário e sessão
mantida ao atualizar a página.

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

Os testes cobrem login, cadastro, consulta do usuário, restauração da
sessão e logout. As respostas da API são simuladas, portanto o backend
e o banco não precisam estar ligados.

## Formatar e verificar a compilação

Dentro de `Frontend/`:

```bash
npm run format
npm run build
```

## Encerrar a aplicação

Na raiz:

```bash
docker compose down
```

Os dados do banco são preservados.