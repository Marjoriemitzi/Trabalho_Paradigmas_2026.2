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


@pytest.mark.asyncio
async def test_list_and_update_transfers(ac_login):
    ac, headers = ac_login

    # Criar contas
    c1 = (
        await ac.post(
            "/api/v1/accounts", json={"name": "C1", "kind": "checking"}, headers=headers
        )
    ).json()["id"]
    c2 = (
        await ac.post(
            "/api/v1/accounts", json={"name": "C2", "kind": "checking"}, headers=headers
        )
    ).json()["id"]

    # Criar Transfer
    res = await ac.post(
        "/api/v1/transfers",
        json={
            "from_account_id": c1,
            "to_account_id": c2,
            "amount_cents": 5000,
            "description": "T",
            "occurred_on": "2026-11-05",
        },
        headers=headers,
    )
    t_id = res.json()["id"]

    # Listar
    res_list = await ac.get(
        "/api/v1/transfers?from=2026-11-01&to=2026-11-30", headers=headers
    )
    assert res_list.status_code == 200
    assert len(res_list.json()["transfers"]) == 1

    # Atualizar (corrige o valor para 6000)
    res_up = await ac.put(
        f"/api/v1/transfers/{t_id}",
        json={
            "from_account_id": c1,
            "to_account_id": c2,
            "amount_cents": 6000,
            "description": "T2",
            "occurred_on": "2026-11-06",
        },
        headers=headers,
    )
    assert res_up.status_code == 200
    assert res_up.json()["amount_cents"] == 6000
    assert res_up.headers["cache-control"] == "no-store"
