import importlib
import uuid
from collections.abc import Callable
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import TextClause, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.schema import CreateSchema, DropSchema

from app.shared.infrastructure.persistence.database import Base

BACKEND = Path(__file__).resolve().parents[3]
ALEMBIC_INI = BACKEND / "alembic.ini"
MODELS_GLOB = "*/infrastructure/persistence/models"

PRIVILEGIOS_DML = ("SELECT", "INSERT", "UPDATE", "DELETE")
TABELAS_BASE_ESPERADAS = frozenset(
    {"users", "accounts", "categories", "transactions", "transfers"}
)
_CONSULTA_REVISAO_ATUAL = text("SELECT version_num FROM alembic_version")
_CONSULTA_REVISAO_PUBLIC = text("SELECT version_num FROM public.alembic_version")


def _carregar_todos_os_modelos() -> None:
    src_app = BACKEND / "src" / "app"
    for models_dir in sorted(src_app.glob(MODELS_GLOB)):
        contexto = models_dir.relative_to(src_app).parts[0]
        for arquivo in sorted(models_dir.glob("*.py")):
            if arquivo.name.startswith("_"):
                continue
            modulo = f"app.{contexto}.infrastructure.persistence.models.{arquivo.stem}"
            importlib.import_module(modulo)


def _rodar_alembic(
    sync_conn: Connection,
    acao: Callable[[Config], None],
    *,
    version_table_schema: str | None,
) -> None:
    cfg = Config(str(ALEMBIC_INI))
    cfg.attributes["connection"] = sync_conn
    cfg.attributes["version_table_schema"] = version_table_schema
    acao(cfg)


async def _tabelas_no_schema(engine: AsyncEngine, schema: str) -> set[str]:
    async with engine.connect() as conn:
        rows = await conn.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname = :schema"),
            {"schema": schema},
        )
        return set(rows.scalars().all())


async def _revisoes_em(engine: AsyncEngine, consulta: TextClause) -> list[str]:
    async with engine.connect() as conn:
        rows = await conn.execute(consulta)
        return list(rows.scalars().all())


async def test_role_da_aplicacao_tem_privilegios_minimos(
    connection: AsyncConnection,
) -> None:
    row = (
        (
            await connection.execute(
                text(
                    "SELECT current_user AS usuario, rolsuper, rolcreatedb, "
                    "rolcreaterole, rolbypassrls, rolreplication "
                    "FROM pg_roles WHERE rolname = current_user"
                )
            )
        )
        .mappings()
        .one()
    )

    flags_proibidas = (
        "rolsuper",
        "rolcreatedb",
        "rolcreaterole",
        "rolbypassrls",
        "rolreplication",
    )
    privilegios_ativos = [flag for flag in flags_proibidas if row[flag]]
    msg = f"{row['usuario']} possui privilégios proibidos: {privilegios_ativos}"
    assert privilegios_ativos == [], msg


async def test_role_da_aplicacao_tem_dml_em_todas_as_tabelas_do_modelo(
    connection: AsyncConnection,
) -> None:
    _carregar_todos_os_modelos()
    tabelas = Base.metadata.tables
    assert tabelas, "Base.metadata.tables não pode estar vazia"
    assert set(tabelas) >= TABELAS_BASE_ESPERADAS, (
        "Tabelas esperadas ausentes em Base.metadata: "
        f"{sorted(TABELAS_BASE_ESPERADAS - set(tabelas))}"
    )

    consulta_privilegio = text(
        "SELECT has_table_privilege("
        "current_user, "
        "format('%I.%I', CAST(:schema AS text), CAST(:tabela AS text)), "
        "CAST(:privilegio AS text)"
        ")"
    )
    faltando: list[tuple[str, str]] = []
    for table in sorted(tabelas.values(), key=lambda t: t.name):
        schema = table.schema or "public"
        # Verifica cada privilégio isoladamente: has_table_privilege com lista
        # separada por vírgula usa semântica OR no PostgreSQL, não AND.
        for privilegio in PRIVILEGIOS_DML:
            permitido: bool = (
                await connection.execute(
                    consulta_privilegio,
                    {
                        "schema": schema,
                        "tabela": table.name,
                        "privilegio": privilegio,
                    },
                )
            ).scalar_one()
            if not permitido:
                faltando.append((f"{schema}.{table.name}", privilegio))

    assert faltando == [], f"Privilégios DML ausentes para current_user: {faltando}"


def test_models_e_migrations_nao_tem_drift(migrated_database: str) -> None:
    _carregar_todos_os_modelos()
    command.check(Config(str(ALEMBIC_INI)))


async def test_migrations_suportam_upgrade_downgrade_e_upgrade_em_schema_isolado(
    migrated_database: str,
) -> None:
    _carregar_todos_os_modelos()
    tabelas_esperadas = {table.name for table in Base.metadata.tables.values()}
    assert tabelas_esperadas

    schema_temp = f"test_mig_{uuid.uuid4().hex}"
    admin_engine = create_async_engine(migrated_database, poolclass=NullPool)
    isolated_engine: AsyncEngine | None = None

    try:
        revisoes_public_antes = await _revisoes_em(
            admin_engine, _CONSULTA_REVISAO_PUBLIC
        )
        assert len(revisoes_public_antes) == 1
        head_public_antes = revisoes_public_antes[0]

        async with admin_engine.begin() as conn:
            await conn.execute(CreateSchema(schema_temp))

        isolated_engine = create_async_engine(
            migrated_database,
            poolclass=NullPool,
            connect_args={"server_settings": {"search_path": schema_temp}},
        )

        # 1. upgrade head no schema temporário
        async with isolated_engine.connect() as conn:
            await conn.run_sync(
                _rodar_alembic,
                lambda cfg: command.upgrade(cfg, "head"),
                version_table_schema=schema_temp,
            )

        tabelas_apos_upgrade = await _tabelas_no_schema(isolated_engine, schema_temp)
        assert tabelas_apos_upgrade >= tabelas_esperadas
        assert "alembic_version" in tabelas_apos_upgrade

        # 2. downgrade base no schema temporário
        async with isolated_engine.connect() as conn:
            await conn.run_sync(
                _rodar_alembic,
                lambda cfg: command.downgrade(cfg, "base"),
                version_table_schema=schema_temp,
            )

        tabelas_apos_downgrade = await _tabelas_no_schema(isolated_engine, schema_temp)
        assert tabelas_apos_downgrade - {"alembic_version"} == set()
        assert await _revisoes_em(isolated_engine, _CONSULTA_REVISAO_ATUAL) == []

        # 3. upgrade head novamente no schema temporário
        async with isolated_engine.connect() as conn:
            await conn.run_sync(
                _rodar_alembic,
                lambda cfg: command.upgrade(cfg, "head"),
                version_table_schema=schema_temp,
            )

        tabelas_recriadas = await _tabelas_no_schema(isolated_engine, schema_temp)
        assert tabelas_recriadas >= tabelas_esperadas
        assert await _revisoes_em(isolated_engine, _CONSULTA_REVISAO_ATUAL) == [
            head_public_antes
        ]

        # 4. alembic check contra o schema recriado (version_table_schema=None
        # corresponde a schemas={None} do autogenerate quando search_path é schema_temp)
        async with isolated_engine.connect() as conn:
            await conn.run_sync(
                _rodar_alembic,
                command.check,
                version_table_schema=None,
            )

        # 5. Confirma que public permaneceu intacto
        revisoes_public_depois = await _revisoes_em(
            admin_engine, _CONSULTA_REVISAO_PUBLIC
        )
        tabelas_public_depois = await _tabelas_no_schema(admin_engine, "public")
        assert revisoes_public_depois == revisoes_public_antes
        assert tabelas_public_depois >= tabelas_esperadas
    finally:
        if isolated_engine is not None:
            await isolated_engine.dispose()
        async with admin_engine.begin() as conn:
            await conn.execute(DropSchema(schema_temp, cascade=True, if_exists=True))
        await admin_engine.dispose()
