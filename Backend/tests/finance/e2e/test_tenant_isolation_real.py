import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from app.users.infrastructure.persistence.models.user_model import UserModel

ACCOUNTS_URL = "/api/v1/accounts"
TRANSACTIONS_URL = "/api/v1/transactions"
TRANSFERS_URL = "/api/v1/transfers"
NOVEMBRO = {"from": "2026-11-01", "to": "2026-11-30"}
SENHA = "S3nha!Forte123"


@asynccontextmanager
async def _usuario_autenticado(
    client: AsyncClient, database_url: str
) -> AsyncIterator[dict[str, str]]:
    email = f"isolamento-{uuid.uuid4().hex}@acme.com"
    credenciais = {"email": email, "password": SENHA}
    try:
        criado = await client.post("/api/v1/users", json=credenciais)
        assert criado.status_code == 201
        login = await client.post("/api/v1/auth/login", json=credenciais)
        assert login.status_code == 200
        yield {"Authorization": f"Bearer {login.json()['access_token']}"}
    finally:
        engine = create_async_engine(database_url, poolclass=NullPool)
        try:
            async with engine.begin() as conn:
                await conn.execute(delete(UserModel).where(UserModel.email == email))
        finally:
            await engine.dispose()


@pytest.fixture
async def usuario_a(
    real_client: AsyncClient, migrated_database: str
) -> AsyncIterator[dict[str, str]]:
    async with _usuario_autenticado(real_client, migrated_database) as headers:
        yield headers


@pytest.fixture
async def usuario_b(
    real_client: AsyncClient, migrated_database: str
) -> AsyncIterator[dict[str, str]]:
    async with _usuario_autenticado(real_client, migrated_database) as headers:
        yield headers


async def abrir_conta(
    client: AsyncClient, headers: dict[str, str], nome: str, kind: str = "checking"
) -> str:
    resposta = await client.post(
        ACCOUNTS_URL, json={"name": nome, "kind": kind}, headers=headers
    )
    assert resposta.status_code == 201
    return str(resposta.json()["id"])


async def saldos(client: AsyncClient, headers: dict[str, str]) -> dict[str, int]:
    resposta = await client.get(ACCOUNTS_URL, headers=headers)
    assert resposta.status_code == 200
    return {c["name"]: c["balance_cents"] for c in resposta.json()["accounts"]}


async def lancar(
    client: AsyncClient,
    headers: dict[str, str],
    conta: str,
    kind: str,
    cents: int,
    descricao: str = "Lançamento",
    dia: str = "2026-11-07",
) -> str:
    resposta = await client.post(
        TRANSACTIONS_URL,
        json={
            "account_id": conta,
            "kind": kind,
            "amount_cents": cents,
            "description": descricao,
            "occurred_on": dia,
        },
        headers=headers,
    )
    assert resposta.status_code == 201
    return str(resposta.json()["id"])


async def transferir(
    client: AsyncClient,
    headers: dict[str, str],
    origem: str,
    destino: str,
    cents: int,
    descricao: str = "Transferência",
    dia: str = "2026-11-10",
) -> str:
    resposta = await client.post(
        TRANSFERS_URL,
        json={
            "from_account_id": origem,
            "to_account_id": destino,
            "amount_cents": cents,
            "description": descricao,
            "occurred_on": dia,
        },
        headers=headers,
    )
    assert resposta.status_code == 201
    return str(resposta.json()["id"])


async def test_listar_contas_nao_expoe_contas_de_outro_usuario(
    real_client: AsyncClient,
    usuario_a: dict[str, str],
    usuario_b: dict[str, str],
) -> None:
    conta_a = await abrir_conta(real_client, usuario_a, "Conta Secreta A")
    await lancar(real_client, usuario_a, conta_a, "income", 50000, "Depósito A")
    conta_b = await abrir_conta(real_client, usuario_b, "Carteira B", kind="wallet")

    resposta = await real_client.get(ACCOUNTS_URL, headers=usuario_b)

    assert resposta.status_code == 200
    contas_b = resposta.json()["accounts"]
    assert len(contas_b) == 1
    assert contas_b[0]["id"] == conta_b
    assert contas_b[0]["name"] == "Carteira B"
    assert contas_b[0]["balance_cents"] == 0
    assert conta_a not in resposta.text
    assert "Conta Secreta A" not in resposta.text
    assert await saldos(real_client, usuario_a) == {"Conta Secreta A": 50000}


async def test_extrato_geral_nao_lista_transacoes_nem_saldo_de_outro_usuario(
    real_client: AsyncClient,
    usuario_a: dict[str, str],
    usuario_b: dict[str, str],
) -> None:
    conta_a = await abrir_conta(real_client, usuario_a, "Corrente A")
    await lancar(
        real_client, usuario_a, conta_a, "income", 100000, "Saldo A", dia="2026-10-20"
    )
    tx_a = await lancar(
        real_client, usuario_a, conta_a, "expense", 4590, "Compra Secreta A"
    )
    conta_b = await abrir_conta(real_client, usuario_b, "Carteira B", kind="wallet")
    tx_b = await lancar(
        real_client, usuario_b, conta_b, "expense", 1200, "Lanche B", dia="2026-11-08"
    )

    resposta = await real_client.get(
        TRANSACTIONS_URL, params=NOVEMBRO, headers=usuario_b
    )

    assert resposta.status_code == 200
    corpo_b = resposta.json()
    assert corpo_b["opening_balance_cents"] == 0
    assert corpo_b["income_cents"] == 0
    assert corpo_b["expense_cents"] == 1200
    assert corpo_b["closing_balance_cents"] == -1200
    assert [t["id"] for t in corpo_b["transactions"]] == [tx_b]
    assert tx_a not in resposta.text
    assert "Compra Secreta A" not in resposta.text

    extrato_a = await real_client.get(
        TRANSACTIONS_URL, params=NOVEMBRO, headers=usuario_a
    )
    assert extrato_a.status_code == 200
    corpo_a = extrato_a.json()
    assert corpo_a["opening_balance_cents"] == 100000
    assert corpo_a["expense_cents"] == 4590
    assert [t["id"] for t in corpo_a["transactions"]] == [tx_a]


async def test_extrato_filtrado_por_conta_de_outro_usuario_responde_404(
    real_client: AsyncClient,
    usuario_a: dict[str, str],
    usuario_b: dict[str, str],
) -> None:
    conta_a = await abrir_conta(real_client, usuario_a, "Corrente A")
    await lancar(real_client, usuario_a, conta_a, "income", 80000, "Salário Secreto A")

    resposta = await real_client.get(
        TRANSACTIONS_URL,
        params={**NOVEMBRO, "account_id": conta_a},
        headers=usuario_b,
    )

    assert resposta.status_code == 404
    assert resposta.json() == {"error": "account_not_found"}
    assert "Salário Secreto A" not in resposta.text

    extrato_a = await real_client.get(
        TRANSACTIONS_URL,
        params={**NOVEMBRO, "account_id": conta_a},
        headers=usuario_a,
    )
    assert extrato_a.status_code == 200
    assert extrato_a.json()["income_cents"] == 80000


async def test_lancar_transacao_em_conta_de_outro_usuario_responde_422_sem_efeito(
    real_client: AsyncClient,
    usuario_a: dict[str, str],
    usuario_b: dict[str, str],
) -> None:
    conta_a = await abrir_conta(real_client, usuario_a, "Corrente A")
    tx_a = await lancar(real_client, usuario_a, conta_a, "income", 100000, "Receita A")
    await abrir_conta(real_client, usuario_b, "Carteira B", kind="wallet")

    resposta = await real_client.post(
        TRANSACTIONS_URL,
        json={
            "account_id": conta_a,
            "kind": "expense",
            "amount_cents": 5000,
            "description": "Tentativa cruzada",
            "occurred_on": "2026-11-07",
        },
        headers=usuario_b,
    )

    assert resposta.status_code == 422
    assert resposta.json() == {
        "error": "invalid_transaction",
        "fields": [{"field": "account_id", "problem": "not_found"}],
    }
    assert await saldos(real_client, usuario_a) == {"Corrente A": 100000}
    assert await saldos(real_client, usuario_b) == {"Carteira B": 0}
    extrato_a = await real_client.get(
        TRANSACTIONS_URL, params=NOVEMBRO, headers=usuario_a
    )
    assert [t["id"] for t in extrato_a.json()["transactions"]] == [tx_a]
    extrato_b = await real_client.get(
        TRANSACTIONS_URL, params=NOVEMBRO, headers=usuario_b
    )
    assert extrato_b.json()["transactions"] == []


async def test_mover_transacao_propria_para_conta_alheia_responde_422_e_mantem_intacta(
    real_client: AsyncClient,
    usuario_a: dict[str, str],
    usuario_b: dict[str, str],
) -> None:
    conta_a = await abrir_conta(real_client, usuario_a, "Corrente A")
    await lancar(real_client, usuario_a, conta_a, "income", 100000, "Receita A")
    conta_b = await abrir_conta(real_client, usuario_b, "Carteira B", kind="wallet")
    tx_b = await lancar(real_client, usuario_b, conta_b, "expense", 2500, "Café B")

    resposta = await real_client.put(
        f"{TRANSACTIONS_URL}/{tx_b}",
        json={
            "account_id": conta_a,
            "kind": "expense",
            "amount_cents": 9999,
            "description": "Movida",
            "occurred_on": "2026-11-08",
        },
        headers=usuario_b,
    )

    assert resposta.status_code == 422
    assert resposta.json() == {
        "error": "invalid_transaction",
        "fields": [{"field": "account_id", "problem": "not_found"}],
    }
    extrato_b = await real_client.get(
        TRANSACTIONS_URL, params=NOVEMBRO, headers=usuario_b
    )
    [gravada_b] = extrato_b.json()["transactions"]
    assert gravada_b["id"] == tx_b
    assert gravada_b["account_id"] == conta_b
    assert gravada_b["amount_cents"] == 2500
    assert gravada_b["description"] == "Café B"
    assert gravada_b["occurred_on"] == "2026-11-07"
    assert await saldos(real_client, usuario_a) == {"Corrente A": 100000}


async def test_alterar_transacao_de_outro_usuario_com_conta_propria_responde_404(
    real_client: AsyncClient,
    usuario_a: dict[str, str],
    usuario_b: dict[str, str],
) -> None:
    conta_a = await abrir_conta(real_client, usuario_a, "Corrente A")
    tx_a = await lancar(real_client, usuario_a, conta_a, "expense", 4590, "Padaria A")
    conta_b = await abrir_conta(real_client, usuario_b, "Carteira B", kind="wallet")

    resposta = await real_client.put(
        f"{TRANSACTIONS_URL}/{tx_a}",
        json={
            "account_id": conta_b,
            "kind": "expense",
            "amount_cents": 100,
            "description": "Adulterada",
            "occurred_on": "2026-11-08",
        },
        headers=usuario_b,
    )

    assert resposta.status_code == 404
    assert resposta.json() == {"error": "transaction_not_found"}
    extrato_a = await real_client.get(
        TRANSACTIONS_URL, params=NOVEMBRO, headers=usuario_a
    )
    [gravada_a] = extrato_a.json()["transactions"]
    assert gravada_a["id"] == tx_a
    assert gravada_a["account_id"] == conta_a
    assert gravada_a["amount_cents"] == 4590
    assert gravada_a["description"] == "Padaria A"
    assert gravada_a["occurred_on"] == "2026-11-07"
    assert await saldos(real_client, usuario_b) == {"Carteira B": 0}


async def test_apagar_transacao_de_outro_usuario_responde_404_e_mantem_no_extrato(
    real_client: AsyncClient,
    usuario_a: dict[str, str],
    usuario_b: dict[str, str],
) -> None:
    conta_a = await abrir_conta(real_client, usuario_a, "Corrente A")
    tx_a = await lancar(real_client, usuario_a, conta_a, "expense", 4590, "Padaria A")

    resposta = await real_client.delete(f"{TRANSACTIONS_URL}/{tx_a}", headers=usuario_b)

    assert resposta.status_code == 404
    assert resposta.json() == {"error": "transaction_not_found"}
    extrato_a = await real_client.get(
        TRANSACTIONS_URL, params=NOVEMBRO, headers=usuario_a
    )
    assert [t["id"] for t in extrato_a.json()["transactions"]] == [tx_a]
    assert await saldos(real_client, usuario_a) == {"Corrente A": -4590}


@pytest.mark.parametrize("campo_alheio", ["to_account_id", "from_account_id"])
async def test_transferencia_com_conta_alheia_responde_422_sem_alterar_saldos(
    real_client: AsyncClient,
    usuario_a: dict[str, str],
    usuario_b: dict[str, str],
    campo_alheio: str,
) -> None:
    conta_a = await abrir_conta(real_client, usuario_a, "Corrente A")
    await lancar(real_client, usuario_a, conta_a, "income", 100000, "Receita A")
    conta_b = await abrir_conta(real_client, usuario_b, "Corrente B")
    await lancar(real_client, usuario_b, conta_b, "income", 50000, "Receita B")
    if campo_alheio == "to_account_id":
        origem, destino = conta_b, conta_a
    else:
        origem, destino = conta_a, conta_b

    resposta = await real_client.post(
        TRANSFERS_URL,
        json={
            "from_account_id": origem,
            "to_account_id": destino,
            "amount_cents": 15000,
            "description": "Transferência cruzada",
            "occurred_on": "2026-11-10",
        },
        headers=usuario_b,
    )

    assert resposta.status_code == 422
    assert resposta.json() == {
        "error": "invalid_transfer",
        "fields": [{"field": campo_alheio, "problem": "not_found"}],
    }
    assert await saldos(real_client, usuario_a) == {"Corrente A": 100000}
    assert await saldos(real_client, usuario_b) == {"Corrente B": 50000}
    lista_a = await real_client.get(TRANSFERS_URL, params=NOVEMBRO, headers=usuario_a)
    lista_b = await real_client.get(TRANSFERS_URL, params=NOVEMBRO, headers=usuario_b)
    assert lista_a.json()["transfers"] == []
    assert lista_b.json()["transfers"] == []


async def test_apagar_transferencia_de_outro_usuario_responde_404_e_mantem_intacta(
    real_client: AsyncClient,
    usuario_a: dict[str, str],
    usuario_b: dict[str, str],
) -> None:
    corrente_a = await abrir_conta(real_client, usuario_a, "Corrente A")
    cartao_a = await abrir_conta(real_client, usuario_a, "Cartão A", kind="credit_card")
    await lancar(real_client, usuario_a, corrente_a, "income", 500000, "Salário A")
    transfer_a = await transferir(
        real_client, usuario_a, corrente_a, cartao_a, 150000, "Fatura A"
    )
    assert await saldos(real_client, usuario_a) == {
        "Cartão A": 150000,
        "Corrente A": 350000,
    }

    resposta = await real_client.delete(
        f"{TRANSFERS_URL}/{transfer_a}", headers=usuario_b
    )

    assert resposta.status_code == 404
    assert resposta.json() == {"error": "transfer_not_found"}
    assert await saldos(real_client, usuario_a) == {
        "Cartão A": 150000,
        "Corrente A": 350000,
    }
    lista_a = await real_client.get(TRANSFERS_URL, params=NOVEMBRO, headers=usuario_a)
    assert [t["id"] for t in lista_a.json()["transfers"]] == [transfer_a]
    lista_b = await real_client.get(TRANSFERS_URL, params=NOVEMBRO, headers=usuario_b)
    assert lista_b.json()["transfers"] == []
