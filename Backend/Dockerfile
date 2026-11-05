# syntax=docker/dockerfile:1
#
# Estágios:
#   builder-*  instalam as dependências num venv (com compilador, que não vai para a imagem final)
#   dev        imagem usada pelo docker compose / Dev Container (inclui ferramentas de dev)
#   runtime    imagem de produção (padrão: é o último estágio)
#
# A imagem base é fixada por digest para que não mude sem você saber.
# Para atualizar: docker pull python:3.12-slim && docker inspect --format '{{index .RepoDigests 0}}' python:3.12-slim
ARG PYTHON_IMAGE=python:3.12-slim@sha256:aa943ce411423c7582288f18707ff66eddcbaeb510502d747a72aeb34f30d159

# ---------------------------------------------------------------------------
FROM ${PYTHON_IMAGE} AS builder-base

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

ENV POETRY_VERSION=2.5.1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# O Poetry fica isolado no próprio venv e nunca é copiado para a imagem final.
RUN python -m venv /opt/poetry \
    && /opt/poetry/bin/pip install "poetry==${POETRY_VERSION}"

# Venv da aplicação: o Poetry instala aqui porque ele está "ativado" via VIRTUAL_ENV/PATH.
RUN python -m venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH

WORKDIR /build
COPY pyproject.toml poetry.lock ./

# ---------------------------------------------------------------------------
FROM builder-base AS builder-prod
# O Poetry confere os hashes sha256 do poetry.lock antes de instalar.
RUN /opt/poetry/bin/poetry install --only main --no-root

FROM builder-base AS builder-dev
RUN /opt/poetry/bin/poetry install --no-root

# ---------------------------------------------------------------------------
FROM ${PYTHON_IMAGE} AS runtime-base

RUN apt-get update \
    && apt-get install -y --no-install-recommends swi-prolog-nox \
    && rm -rf /var/lib/apt/lists/*

# Usuário sem privilégios. UID/GID 1000 = mesmo usuário do host (WSL), para os arquivos
# do bind mount não ficarem com dono root.
ARG APP_UID=1000
ARG APP_GID=1000
RUN groupadd --gid "${APP_GID}" app \
    && useradd --uid "${APP_UID}" --gid app --create-home --shell /usr/sbin/nologin app

ENV VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH \
    PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PROLOG_RULES_DIR=/app/rules

# /app pertence ao root e é só leitura para o usuário "app".
WORKDIR /app
EXPOSE 8000

# ---------------------------------------------------------------------------
FROM runtime-base AS dev
COPY --from=builder-dev /opt/venv /opt/venv
# Poetry só na imagem de dev, para gerenciar dependências sem Python no host.
COPY --from=builder-base /opt/poetry /opt/poetry
RUN ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry \
    && usermod --shell /bin/bash app
ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1
USER app
CMD ["uvicorn", "finance_manager.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ---------------------------------------------------------------------------
FROM runtime-base AS runtime
COPY --from=builder-prod /opt/venv /opt/venv
COPY src/ ./src/
COPY rules/ ./rules/
COPY migrations/ ./migrations/
COPY alembic.ini ./
USER app
CMD ["uvicorn", "finance_manager.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header"]
