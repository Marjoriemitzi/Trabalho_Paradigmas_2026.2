# Trabalho_Paradigmas_2026.2

Gerenciador de finanças pessoais. Monorepo com:

| Pasta       | O que é                                 | Detalhes                                 |
| ----------- | --------------------------------------- | ---------------------------------------- |
| `Backend/`  | API em FastAPI + Prolog, com PostgreSQL | [Backend/README.md](Backend/README.md), [CONTRIBUTING](Backend/CONTRIBUTING.md) |
| `Frontend/` | Interface em Elm                        | [Frontend/README.md](Frontend/README.md) |

Na raiz ficam os arquivos do projeto todo:

| Arquivo                  | Para quê                                                |
| ------------------------ | ------------------------------------------------------- |
| `docker-compose.yml`     | sobe API, banco (e depois o frontend) com um só comando |
| `.env` / `.env.example`  | senhas e configurações usadas pelo `docker-compose.yml` |
| `scripts/git-hooks/`     | hook de commit que checa cada parte alterada            |
| `.devcontainer/<parte>/` | Dev Containers do VS Code, um por parte                 |

**Todos os comandos `docker compose` rodam na raiz.**

## Requisitos

- git
- Docker com Docker Compose v2
  - No Windows/WSL2: Docker Desktop → Settings → Resources → **WSL Integration** → ative a sua distro.

## Setup depois do clone

```bash
git clone git@github.com:Marjoriemitzi/Trabalho_Paradigmas_2026.2.git
cd Trabalho_Paradigmas_2026.2
```

**1. Crie o `.env` com senhas fortes.**

Ele nunca vai para o git.

```bash
cp .env.example .env && chmod 600 .env
sed -i "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$(openssl rand -hex 32)/; s/^APP_DB_PASSWORD=.*/APP_DB_PASSWORD=$(openssl rand -hex 32)/; s/^JWT_SECRET=.*/JWT_SECRET=$(openssl rand -hex 32)/" .env
```

**2. Construa e suba os containers.**

```bash
docker compose build
docker compose up -d
docker compose ps                          # app = running, db = healthy
curl http://127.0.0.1:8000/health          # {"status":"ok"}
```

**3. Instale o hook de commit.**

Ele checa só as partes que o commit altera (o backend roda ruff e mypy dentro do container). Instale por **cópia** (não por link), para que uma alteração no script não passe a rodar no seu computador sem você saber. Repita o comando sempre que `scripts/git-hooks/pre-commit` mudar.

```bash
cp scripts/git-hooks/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
```

**4. Continue no README de cada parte**

Migrations e verificações do backend e etc.

## Dia a dia

```bash
docker compose up -d                       # subir
docker compose down                        # parar (mantém os dados)
docker compose logs -f app                 # logs da API
```

Antes de cada commit, confira com `git status` que o `.env` não aparece.

## CI

O workflow [`.github/workflows/backend.yml`](.github/workflows/backend.yml) roda em todo PR para a
`main` e em todo push na `main` que mexa em `Backend/`, `docker-compose.yml`, `.env.example` ou no
próprio workflow. Ele gera o `.env` com segredos novos, sobe o banco e a API no Docker e roda, nesta
ordem: `alembic upgrade head`, `alembic check`, `alembic downgrade base` + `upgrade head`,
`ruff format --check` e `task check` (ruff, mypy, pytest e pip-audit). O resultado aparece na aba
**Checks** do PR; o check se chama `backend`. Um PR que só mexe em `Frontend/` fica verde sem rodar
o job.

O `pip-audit` consulta a internet: se aparecer uma vulnerabilidade nova numa dependência, o CI fica
vermelho mesmo sem mudança de código. Isso é esperado, e a correção é atualizar a dependência
(`docker compose run --rm --no-deps tools poetry update --lock <pacote>`).
