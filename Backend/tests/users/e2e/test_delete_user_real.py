import uuid

from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

URL = "/api/v1/users/me"
SENHA = "S3nha!Forte123"


async def contar(banco: str, usuario: str) -> dict[str, int]:
    engine = create_async_engine(banco, poolclass=NullPool)
    async with engine.connect() as conn:
        resultado = {}
        for tabela, coluna in (
            ("users", "id"),
            ("accounts", "owner_id"),
            ("transactions", "owner_id"),
            ("transfers", "owner_id"),
            ("recurrences", "owner_id"),
        ):
            consulta = text(f"SELECT count(*) FROM {tabela} WHERE {coluna} = :u")  # noqa: S608
            resultado[tabela] = await conn.scalar(consulta, {"u": uuid.UUID(usuario)})
    await engine.dispose()
    return resultado


async def preparar_dados(
    client: AsyncClient, headers: dict[str, str]
) -> tuple[str, str]:
    contas = []
    for nome in ("Corrente", "Carteira"):
        resposta = await client.post(
            "/api/v1/accounts", json={"name": nome, "kind": "checking"}, headers=headers
        )
        contas.append(str(resposta.json()["id"]))
    lancamento = {
        "account_id": contas[0],
        "kind": "income",
        "amount_cents": 10000,
        "description": "Salário",
        "occurred_on": "2026-11-05",
    }
    assert (
        await client.post("/api/v1/transactions", json=lancamento, headers=headers)
    ).status_code == 201
    transferencia = {
        "from_account_id": contas[0],
        "to_account_id": contas[1],
        "amount_cents": 2500,
        "description": "Para a carteira",
        "occurred_on": "2026-11-06",
    }
    assert (
        await client.post("/api/v1/transfers", json=transferencia, headers=headers)
    ).status_code == 201
    recorrencia = {
        "account_id": contas[0],
        "kind": "expense",
        "amount_cents": 150000,
        "description": "Aluguel",
        "category": "moradia",
        "frequency": "monthly",
        "day": 10,
        "starts_on": "2026-11-01",
        "ends_on": None,
    }
    assert (
        await client.post("/api/v1/recurrences", json=recorrencia, headers=headers)
    ).status_code == 201
    eu = await client.get(URL, headers=headers)
    return str(eu.json()["id"]), contas[0]


async def test_apagar_a_conta_leva_junto_todos_os_dados_da_pessoa(
    real_client: AsyncClient,
    auth_headers: dict[str, str],
    migrated_database: str,
) -> None:
    usuario, _ = await preparar_dados(real_client, auth_headers)
    antes = await contar(migrated_database, usuario)
    assert antes == {
        "users": 1,
        "accounts": 2,
        "transactions": 1,
        "transfers": 1,
        "recurrences": 1,
    }

    resposta = await real_client.request(
        "DELETE", URL, json={"password": SENHA}, headers=auth_headers
    )

    assert resposta.status_code == 204
    depois = await contar(migrated_database, usuario)
    assert depois == {
        "users": 0,
        "accounts": 0,
        "transactions": 0,
        "transfers": 0,
        "recurrences": 0,
    }


async def test_o_token_antigo_deixa_de_valer_em_todas_as_rotas(
    real_client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await preparar_dados(real_client, auth_headers)
    await real_client.request(
        "DELETE", URL, json={"password": SENHA}, headers=auth_headers
    )

    perfil = await real_client.get(URL, headers=auth_headers)
    contas = await real_client.get("/api/v1/accounts", headers=auth_headers)
    nova_conta = await real_client.post(
        "/api/v1/accounts",
        json={"name": "Fantasma", "kind": "wallet"},
        headers=auth_headers,
    )

    for resposta in (perfil, contas, nova_conta):
        assert resposta.status_code == 401
        assert resposta.json() == {"error": "invalid_token"}


async def test_o_mesmo_email_pode_se_cadastrar_de_novo(
    real_client: AsyncClient, auth_headers: dict[str, str], fresh_email: str
) -> None:
    await real_client.request(
        "DELETE", URL, json={"password": SENHA}, headers=auth_headers
    )

    de_novo = await real_client.post(
        "/api/v1/users", json={"email": fresh_email, "password": SENHA}
    )

    assert de_novo.status_code == 201


async def test_senha_errada_nao_apaga_nada(
    real_client: AsyncClient,
    auth_headers: dict[str, str],
    migrated_database: str,
) -> None:
    usuario, _ = await preparar_dados(real_client, auth_headers)

    resposta = await real_client.request(
        "DELETE", URL, json={"password": "errada"}, headers=auth_headers
    )

    assert resposta.status_code == 422
    assert resposta.json() == {"error": "invalid_current_password"}
    assert await contar(migrated_database, usuario) == {
        "users": 1,
        "accounts": 2,
        "transactions": 1,
        "transfers": 1,
        "recurrences": 1,
    }
