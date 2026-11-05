"""Entrada da aplicação. Versão mínima para validar o setup."""

import os

from fastapi import FastAPI

# Documentação interativa desligada por padrão (seguro para produção).
# Em desenvolvimento, defina ENABLE_DOCS=true no .env.
_docs_enabled = os.getenv("ENABLE_DOCS", "false").strip().lower() == "true"

app = FastAPI(
    title="Gerenciador de Finanças Pessoais",
    docs_url="/docs" if _docs_enabled else None,
    redoc_url="/redoc" if _docs_enabled else None,
    openapi_url="/openapi.json" if _docs_enabled else None,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
