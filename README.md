# Trabalho_Paradigmas_2026.2

Gerenciador de finanças pessoais. Monorepo com:

| Pasta       | O que é                                 | Detalhes                                      |
|-------------|-----------------------------------------|-----------------------------------------------|
| `Backend/`  | API em FastAPI + Prolog, com PostgreSQL | [Backend/README.md](Backend/README.md)        |
| `Frontend/` | Interface em Elm                        | [Frontend/README.md](Frontend/README.md)      |

Na raiz ficam os arquivos do projeto todo:

| Arquivo                      | Para quê                                                   |
|------------------------------|------------------------------------------------------------|
| `docker-compose.yml`         | sobe API, banco (e depois o frontend) com um só comando     |
| `.env` / `.env.example`      | senhas e configurações usadas pelo `docker-compose.yml`    |
| `scripts/git-hooks/`         | hook de commit que checa cada parte alterada               |
| `.devcontainer/<parte>/`     | Dev Containers do VS Code, um por parte                    |

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

**1. Crie o `.env` com senhas fortes.** Ele nunca vai para o git.

```bash
cp .env.example .env && chmod 600 .env
sed -i "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$(openssl rand -hex 32)/; s/^APP_DB_PASSWORD=.*/APP_DB_PASSWORD=$(openssl rand -hex 32)/" .env
```

**2. Construa e suba os containers.**

```bash
docker compose build
docker compose up -d
docker compose ps                          # app = running, db = healthy
curl http://127.0.0.1:8000/health          # {"status":"ok"}
```

**3. Instale o hook de commit.** Ele checa só as partes que o commit altera (o backend roda
ruff e mypy dentro do container). Instale por **cópia** (não por link), para que uma alteração
no script não passe a rodar no seu computador sem você saber. Repita o comando sempre que
`scripts/git-hooks/pre-commit` mudar.

```bash
cp scripts/git-hooks/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
```

**4. Continue no README de cada parte** (migrations e verificações do backend etc.).

## Dia a dia

```bash
docker compose up -d                       # subir
docker compose down                        # parar (mantém os dados)
docker compose logs -f app                 # logs da API
```

Antes de cada commit, confira com `git status` que o `.env` não aparece.
