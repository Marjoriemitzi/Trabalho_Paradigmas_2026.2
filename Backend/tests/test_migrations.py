from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"


def test_as_migrations_tem_uma_ponta_so() -> None:
    config = Config(str(ALEMBIC_INI))

    pontas = ScriptDirectory.from_config(config).get_heads()

    assert len(pontas) == 1, f"Migrations com mais de uma ponta: {pontas}"
