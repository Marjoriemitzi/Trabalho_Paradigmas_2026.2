"""Grava o contrato OpenAPI num arquivo versionado: `task openapi`."""

import json
import sys
from collections.abc import Sequence
from pathlib import Path

from app.main import create_app
from app.shared.infrastructure.config.settings import Settings


def render_openapi(settings: Settings) -> str:
    """O esquema em JSON determinístico: o diff só muda quando o contrato muda."""
    esquema = create_app(settings).openapi()
    return json.dumps(esquema, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def main(argv: Sequence[str]) -> int:
    if len(argv) != 1:
        sys.stderr.write("uso: python -m app.export_openapi <arquivo.json>\n")
        return 2
    destino = Path(argv[0])
    destino.write_text(render_openapi(Settings()), encoding="utf-8")
    sys.stdout.write(f"OpenAPI gravado em {destino}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
