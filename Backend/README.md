# Backend — Gerenciador de Finanças Pessoais

Backend em FastAPI + Prolog, Clean Architecture + DDD.

Todo o backend roda dentro do Docker: a API, o banco, os testes, o lint e as migrations.
Nenhuma dependência Python do projeto é instalada fora dos containers.

> **Os comandos `docker compose` deste README rodam na raiz do monorepo**, onde fica o
> `docker-compose.yml`. O setup inicial (`.env`, subir os containers, hook de commit) está no
> [README da raiz](../README.md).

> ⚠️ Não rode `poetry install`, `pip install` ou `poetry run ...` no seu computador. Se a pasta
> `.venv/` aparecer no projeto, apague-a: código dentro dela poderia ser alterado de dentro do
> Dev Container e depois executado fora dele.

## Primeira execução

Depois do setup da raiz, aplique as migrations e rode as verificações. O resultado esperado é
`All checks passed!`, `Success: no issues found`, todos os testes passando e
`No known vulnerabilities found`.

```bash
docker compose exec app alembic upgrade head
docker compose exec app alembic current
docker compose exec app task check
```

Na primeira subida, o banco cria sozinho o usuário da aplicação (`Backend/db/init/`).

A API fica em http://127.0.0.1:8000. A documentação fica em `/docs` quando `ENABLE_DOCS=true`
no `.env`.

## Dia a dia

```bash
docker compose up -d                       # subir (o código recarrega sozinho ao salvar)
docker compose down                        # parar (mantém os dados)
docker compose logs -f app                 # logs da API
docker compose logs -f db                  # logs do banco
docker compose build                       # depois de mudar dependências ou o Dockerfile
```

## Qualidade

O serviço `app` (a API) é só leitura. Comandos que precisam gravar arquivos do projeto usam o
serviço `tools`: mesma imagem, sem portas, e só sobe quando chamado com `docker compose run`.

```bash
docker compose exec app task check         # tudo: lint + tipos + testes + auditoria
docker compose exec app task lint          # ruff check
docker compose exec app task typecheck     # mypy
docker compose exec app task test          # pytest
docker compose exec app task audit         # vulnerabilidades nas dependências

docker compose run --rm --no-deps tools ruff format .     # formatar o código
```

## Migrations

```bash
docker compose run --rm tools alembic revision --autogenerate -m "descrição"   # gerar migration

docker compose exec app alembic upgrade head
docker compose exec app alembic downgrade -1
docker compose exec app alembic history
```

`migrations/env.py` lê a `DATABASE_URL` do ambiente. Nunca coloque senha no `alembic.ini`.

O `--autogenerate` só funciona depois que `target_metadata` em `migrations/env.py` apontar para o
`MetaData` dos modelos do SQLAlchemy. Até lá, use `alembic revision -m "descrição"` sem ele.

## Dependências

O Poetry existe só dentro da imagem de dev. Os comandos abaixo atualizam o `pyproject.toml` e o
`poetry.lock` sem instalar nada no seu computador. Depois, reconstrua a imagem.

```bash
docker compose run --rm --no-deps tools poetry add --lock <pacote>               # produção
docker compose run --rm --no-deps tools poetry add --lock --group dev <pacote>   # desenvolvimento
docker compose run --rm --no-deps tools poetry update --lock                     # atualizar

docker compose build && docker compose up -d
docker compose exec app task audit
```

## Banco de dados

```bash
docker compose exec db psql -U postgres_admin -d finance    # pede POSTGRES_PASSWORD do .env
docker compose down -v                     # ⚠️ APAGA todos os dados e recria o banco do zero
```

## Dev Container (VS Code)

Abra a raiz do monorepo no VS Code, e então paleta de comandos →
**Dev Containers: Reopen in Container** → escolha **finance-manager (backend)**. O editor, o autocomplete e o
terminal ficam dentro de um container separado da API.

O container monta só a pasta `Backend/`. Os arquivos da raiz que conseguem executar comandos
no seu computador (`.git/`, `.devcontainer/`, `docker-compose.yml`, `scripts/`, `.gitignore`)
nem entram nele. Dentro de `Backend/`, estes ficam **somente leitura** de propósito:
`Dockerfile`, `.gitignore`, `.dockerignore`. Edite-os pelo terminal do host.

Os commits são feitos pelo terminal do host (a imagem não tem git).

## Imagem de produção

```bash
docker build --target runtime -t finance-manager Backend
docker run --rm --read-only --cap-drop ALL --security-opt no-new-privileges:true \
  -p 127.0.0.1:8000:8000 -e DATABASE_URL="postgresql+asyncpg://..." finance-manager
```

A imagem de produção roda sem root, não tem compilador nem ferramentas de dev e deixa `/docs`
desligado por padrão.

## Segurança do ambiente

- As portas são publicadas só em `127.0.0.1`; nada fica visível na rede local.
- A API roda sem root, sem capabilities, com o sistema de arquivos e o código somente leitura.
- A API usa um usuário comum do Postgres (`APP_DB_USER`), nunca o superusuário. O banco exige
  senha em todas as conexões.
- As imagens base são fixadas por digest. Para atualizar:
  ```bash
  docker pull python:3.12-slim && docker inspect --format '{{index .RepoDigests 0}}' python:3.12-slim
  docker pull postgres:16 && docker inspect --format '{{index .RepoDigests 0}}' postgres:16
  ```
  Depois troque o `@sha256:...` no `Backend/Dockerfile` e no `docker-compose.yml` da raiz.
- Antes de cada commit, confira com `git status` que o `.env` não aparece.
- Prolog: nunca monte queries do `pyswip` concatenando texto do usuário (`shell/1` executa
  comandos); passe os valores como variáveis ou átomos validados.
