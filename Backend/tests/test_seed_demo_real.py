import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from app import seed_demo
from app.shared.infrastructure.config.settings import Settings
from app.users.infrastructure.persistence.models.user_model import UserModel

SENHA = "S3nha!Forte123"


async def apagar(banco: str, email: str) -> None:
    engine = create_async_engine(banco, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.execute(delete(UserModel).where(UserModel.email == email))
    await engine.dispose()


@pytest.fixture
def email_novo() -> str:
    return f"demo-{uuid.uuid4().hex}@acme.com"


async def test_o_seed_cria_o_usuario_com_as_contas_e_o_login_funciona(
    real_client: AsyncClient,
    migrated_database: str,
    monkeypatch: pytest.MonkeyPatch,
    email_novo: str,
) -> None:
    monkeypatch.setenv("APP_ENV", "development")
    try:
        resumo = await seed_demo.seed(Settings(), email_novo, SENHA, reset=False)

        login = await real_client.post(
            "/api/v1/auth/login", json={"email": email_novo, "password": SENHA}
        )
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        contas = await real_client.get("/api/v1/accounts", headers=headers)

        assert resumo.generated_password is False
        assert login.status_code == 200
        assert {c["name"] for c in contas.json()["accounts"]} == {
            "Carteira",
            "Conta corrente",
            "Cartão",
        }
    finally:
        await apagar(migrated_database, email_novo)


async def test_o_extrato_de_cada_conta_bate_com_o_saldo(
    real_client: AsyncClient,
    migrated_database: str,
    monkeypatch: pytest.MonkeyPatch,
    email_novo: str,
) -> None:
    monkeypatch.setenv("APP_ENV", "development")
    try:
        await seed_demo.seed(Settings(), email_novo, SENHA, reset=False)
        login = await real_client.post(
            "/api/v1/auth/login", json={"email": email_novo, "password": SENHA}
        )
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        contas = (await real_client.get("/api/v1/accounts", headers=headers)).json()

        for conta in contas["accounts"]:
            extrato = await real_client.get(
                "/api/v1/transactions",
                params={
                    "from": (date.today() - timedelta(days=200)).isoformat(),
                    "to": date.today().isoformat(),
                    "account_id": conta["id"],
                },
                headers=headers,
            )
            assert extrato.json()["closing_balance_cents"] == conta["balance_cents"]
    finally:
        await apagar(migrated_database, email_novo)


async def test_sem_senha_o_seed_gera_uma_senha_forte_que_funciona(
    real_client: AsyncClient,
    migrated_database: str,
    monkeypatch: pytest.MonkeyPatch,
    email_novo: str,
) -> None:
    monkeypatch.setenv("APP_ENV", "development")
    try:
        resumo = await seed_demo.seed(Settings(), email_novo, None, reset=False)

        login = await real_client.post(
            "/api/v1/auth/login",
            json={"email": email_novo, "password": resumo.password},
        )

        assert resumo.generated_password is True
        assert login.status_code == 200
    finally:
        await apagar(migrated_database, email_novo)


async def test_com_o_e_mail_existente_para_e_com_reset_recria_sem_duplicar(
    migrated_database: str, monkeypatch: pytest.MonkeyPatch, email_novo: str
) -> None:
    monkeypatch.setenv("APP_ENV", "development")
    try:
        await seed_demo.seed(Settings(), email_novo, SENHA, reset=False)

        with pytest.raises(seed_demo.SeedError, match="--reset"):
            await seed_demo.seed(Settings(), email_novo, SENHA, reset=False)
        resumo = await seed_demo.seed(Settings(), email_novo, SENHA, reset=True)

        assert resumo.accounts == 3
    finally:
        await apagar(migrated_database, email_novo)


async def test_fora_do_desenvolvimento_recusa_sem_abrir_conexao(
    monkeypatch: pytest.MonkeyPatch, email_novo: str
) -> None:
    def nao_deveria_conectar(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("abriu conexão com o banco")

    monkeypatch.setattr(seed_demo, "create_async_engine", nao_deveria_conectar)
    for ambiente in ("production", "test"):
        monkeypatch.setenv("APP_ENV", ambiente)

        with pytest.raises(seed_demo.SeedError, match="APP_ENV=development"):
            await seed_demo.seed(Settings(), email_novo, SENHA, reset=False)


def test_o_comando_sai_com_codigo_1_quando_o_ambiente_nao_e_desenvolvimento(
    monkeypatch: pytest.MonkeyPatch, email_novo: str
) -> None:
    monkeypatch.delenv("APP_ENV", raising=False)

    assert seed_demo.main(["--email", email_novo]) == 1


def test_a_senha_gerada_passa_na_politica() -> None:
    senha = seed_demo.generate_password()

    assert len(senha) >= 12
    assert any(c.isupper() for c in senha)
    assert any(c.islower() for c in senha)
    assert any(c.isdigit() for c in senha)
    assert any(not c.isalnum() for c in senha)
