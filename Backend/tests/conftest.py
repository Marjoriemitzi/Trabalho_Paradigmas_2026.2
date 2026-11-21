import os
import uuid
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from hypothesis import settings
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.main import create_app
from app.users.infrastructure.persistence.models.user_model import UserModel

BACKEND = Path(__file__).resolve().parents[1]
TESTS_DIR = Path(__file__).resolve().parent
MARKERS: dict[str, pytest.MarkDecorator] = {
    "unit": pytest.mark.unit,
    "contract": pytest.mark.contract,
    "integration": pytest.mark.integration,
    "e2e": pytest.mark.e2e,
    "real": pytest.mark.real,
    "property": pytest.mark.property,
}
SUITE_MARKERS = frozenset(MARKERS)
ROOT_E2E_FILES = frozenset({"test_health.py", "test_cors.py"})

settings.register_profile(
    "ci",
    max_examples=50,
    derandomize=True,
    deadline=None,
    database=None,
)
settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "ci"))

pytest.register_assert_rewrite("tests.users.contracts", "tests.finance.contracts")


def markers_for_path(path: Path, *, is_contract: bool = False) -> tuple[str, ...]:
    try:
        rel = path.resolve().relative_to(TESTS_DIR)
    except ValueError:
        return ()
    nome, partes = rel.name, rel.parts
    if nome.endswith("_real.py"):
        return ("e2e", "real")
    if "unit" in partes:
        return (
            ("unit", "contract")
            if nome.startswith("test_fake_") or is_contract
            else ("unit",)
        )
    if "integration" in partes:
        return (
            ("integration", "contract")
            if nome.startswith("test_sql_") or is_contract
            else ("integration",)
        )
    if "e2e" in partes or (len(partes) == 1 and nome in ROOT_E2E_FILES):
        return ("e2e",)
    return ("unit",) if len(partes) == 1 and nome.startswith("test_") else ()


def _uses_contract(item: pytest.Item) -> bool:
    if not isinstance(item, pytest.Function) or item.cls is None:
        return False
    return any(".contracts." in base.__module__ for base in item.cls.__mro__)


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    sem_marcador: list[str] = []
    for item in items:
        existentes = {m.name for m in item.iter_markers()}
        for nome in markers_for_path(item.path, is_contract=_uses_contract(item)):
            if nome not in existentes:
                item.add_marker(MARKERS[nome])
                existentes.add(nome)
        if not (existentes & SUITE_MARKERS):
            sem_marcador.append(item.nodeid)
    if sem_marcador:
        lista = ", ".join(sem_marcador)
        raise pytest.UsageError(f"Testes sem marcador de suíte registrado: {lista}")


@pytest.fixture(scope="session")
def migrated_database() -> str:
    command.upgrade(Config(str(BACKEND / "alembic.ini")), "head")
    return os.environ["DATABASE_URL"]


@pytest.fixture
async def connection(migrated_database: str) -> AsyncIterator[AsyncConnection]:
    engine = create_async_engine(migrated_database, poolclass=NullPool)
    async with engine.connect() as conn:
        transaction = await conn.begin()
        yield conn
        await transaction.rollback()
    await engine.dispose()


@pytest.fixture
def session_factory(connection: AsyncConnection) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )


@pytest.fixture
async def session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session


def ip_do_teste() -> str:
    """Um IP só deste teste, para o limite de tentativas não juntar os testes reais."""
    return "10." + ".".join(str(b) for b in uuid.uuid4().bytes[:3])


@pytest.fixture
async def real_client(migrated_database: str) -> AsyncIterator[AsyncClient]:
    app = create_app()
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app, client=(ip_do_teste(), 5000))
        async with AsyncClient(transport=transport, base_url="http://teste") as client:
            yield client


@pytest.fixture
async def fresh_email(migrated_database: str) -> AsyncIterator[str]:
    unico = f"e2e-{uuid.uuid4().hex}@acme.com"
    yield unico
    engine = create_async_engine(migrated_database, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.execute(delete(UserModel).where(UserModel.email == unico))
    await engine.dispose()


@pytest.fixture
async def auth_headers(real_client: AsyncClient, fresh_email: str) -> dict[str, str]:
    pedido = {"email": fresh_email, "password": "S3nha!Forte123"}
    assert (await real_client.post("/api/v1/users", json=pedido)).status_code == 201
    resposta = await real_client.post("/api/v1/auth/login", json=pedido)
    assert resposta.status_code == 200
    return {"Authorization": f"Bearer {resposta.json()['access_token']}"}
