from httpx import AsyncClient


async def abrir(
    client: AsyncClient, token: dict[str, str], nome: str, kind: str
) -> str:
    resposta = await client.post(
        "/api/v1/accounts", json={"name": nome, "kind": kind}, headers=token
    )
    return str(resposta.json()["id"])


async def lancar(
    client: AsyncClient, token: dict[str, str], conta: str, kind: str, cents: int
) -> None:
    pedido = {
        "account_id": conta,
        "kind": kind,
        "amount_cents": cents,
        "description": "Lançamento",
        "occurred_on": "2026-11-05",
    }
    resposta = await client.post("/api/v1/transactions", json=pedido, headers=token)
    assert resposta.status_code == 201


async def saldos(client: AsyncClient, token: dict[str, str]) -> dict[str, int]:
    lista = await client.get("/api/v1/accounts", headers=token)
    return {c["name"]: c["balance_cents"] for c in lista.json()["accounts"]}


async def test_pagar_a_fatura_move_o_dinheiro_sem_mudar_o_total(
    real_client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    corrente = await abrir(real_client, auth_headers, "Corrente", "checking")
    cartao = await abrir(real_client, auth_headers, "Cartão", "credit_card")
    await lancar(real_client, auth_headers, corrente, "income", 520000)
    await lancar(real_client, auth_headers, cartao, "expense", 150000)

    criada = await real_client.post(
        "/api/v1/transfers",
        json={
            "from_account_id": corrente,
            "to_account_id": cartao,
            "amount_cents": 150000,
            "description": "Pagamento da fatura",
            "occurred_on": "2026-11-10",
        },
        headers=auth_headers,
    )

    assert criada.status_code == 201
    assert await saldos(real_client, auth_headers) == {
        "Cartão": 0,
        "Corrente": 370000,
    }
    extrato = await real_client.get(
        "/api/v1/transactions",
        params={"from": "2026-11-01", "to": "2026-11-30", "account_id": cartao},
        headers=auth_headers,
    )
    corpo = extrato.json()
    assert corpo["transfers_in_cents"] == 150000
    assert corpo["closing_balance_cents"] == 0
    assert [t["description"] for t in corpo["transfers"]] == ["Pagamento da fatura"]
    total = await real_client.get(
        "/api/v1/transactions",
        params={"from": "2026-11-01", "to": "2026-11-30"},
        headers=auth_headers,
    )
    assert total.json()["transfers"] == []
    assert total.json()["closing_balance_cents"] == 520000 - 150000

    apagada = await real_client.delete(
        f"/api/v1/transfers/{criada.json()['id']}", headers=auth_headers
    )

    assert apagada.status_code == 204
    assert await saldos(real_client, auth_headers) == {
        "Cartão": -150000,
        "Corrente": 520000,
    }


async def test_listar_o_periodo_e_corrigir_o_valor_muda_os_saldos(
    real_client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    corrente = await abrir(real_client, auth_headers, "Corrente", "checking")
    carteira = await abrir(real_client, auth_headers, "Carteira", "wallet")
    await lancar(real_client, auth_headers, corrente, "income", 100000)
    criada = await real_client.post(
        "/api/v1/transfers",
        json={
            "from_account_id": corrente,
            "to_account_id": carteira,
            "amount_cents": 5000,
            "description": "Para a carteira",
            "occurred_on": "2026-11-05",
        },
        headers=auth_headers,
    )
    transfer_id = criada.json()["id"]

    lista = await real_client.get(
        "/api/v1/transfers",
        params={"from": "2026-11-01", "to": "2026-11-30"},
        headers=auth_headers,
    )
    corrigida = await real_client.put(
        f"/api/v1/transfers/{transfer_id}",
        json={
            "from_account_id": corrente,
            "to_account_id": carteira,
            "amount_cents": 6000,
            "description": "Para a carteira",
            "occurred_on": "2026-11-06",
        },
        headers=auth_headers,
    )

    assert lista.status_code == 200
    assert lista.headers["cache-control"] == "no-store"
    assert [t["id"] for t in lista.json()["transfers"]] == [transfer_id]
    assert corrigida.status_code == 200
    assert corrigida.headers["cache-control"] == "no-store"
    assert corrigida.json()["amount_cents"] == 6000
    assert await saldos(real_client, auth_headers) == {
        "Corrente": 94000,
        "Carteira": 6000,
    }


async def test_corrigir_a_transferencia_de_outro_usuario_responde_404(
    real_client: AsyncClient, auth_headers: dict[str, str], intruso: dict[str, str]
) -> None:
    corrente = await abrir(real_client, auth_headers, "Corrente", "checking")
    carteira = await abrir(real_client, auth_headers, "Carteira", "wallet")
    corpo = {
        "from_account_id": corrente,
        "to_account_id": carteira,
        "amount_cents": 5000,
        "description": "Minha",
        "occurred_on": "2026-11-05",
    }
    criada = await real_client.post(
        "/api/v1/transfers", json=corpo, headers=auth_headers
    )

    resposta = await real_client.put(
        f"/api/v1/transfers/{criada.json()['id']}", json=corpo, headers=intruso
    )

    assert resposta.status_code == 404
    assert resposta.json() == {"error": "transfer_not_found"}
