from httpx import AsyncClient

URL = "/api/v1/transactions"


async def lancar(
    client: AsyncClient,
    token: dict[str, str],
    conta: str,
    kind: str,
    cents: int,
    dia: str,
) -> None:
    pedido = {
        "account_id": conta,
        "kind": kind,
        "amount_cents": cents,
        "description": "Lançamento",
        "occurred_on": dia,
    }
    assert (await client.post(URL, json=pedido, headers=token)).status_code == 201


async def test_o_extrato_mostra_o_que_foi_lancado(
    real_client: AsyncClient, auth_headers: dict[str, str], carteira: str
) -> None:
    await lancar(real_client, auth_headers, carteira, "income", 100000, "2026-10-20")
    await lancar(real_client, auth_headers, carteira, "income", 520000, "2026-11-05")
    await lancar(real_client, auth_headers, carteira, "expense", 4590, "2026-11-07")

    resposta = await real_client.get(
        URL, params={"from": "2026-11-01", "to": "2026-11-30"}, headers=auth_headers
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["opening_balance_cents"] == 100000
    assert corpo["income_cents"] == 520000
    assert corpo["expense_cents"] == 4590
    assert corpo["closing_balance_cents"] == 615410
    assert [t["occurred_on"] for t in corpo["transactions"]] == [
        "2026-11-05",
        "2026-11-07",
    ]


async def test_o_extrato_de_uma_conta_so_nao_mistura_as_outras(
    real_client: AsyncClient, auth_headers: dict[str, str], carteira: str
) -> None:
    pedido = {"name": "Nubank", "kind": "checking"}
    criada = await real_client.post(
        "/api/v1/accounts", json=pedido, headers=auth_headers
    )
    nubank = criada.json()["id"]
    await lancar(real_client, auth_headers, carteira, "income", 100000, "2026-10-20")
    await lancar(real_client, auth_headers, nubank, "income", 700000, "2026-10-20")
    await lancar(real_client, auth_headers, nubank, "expense", 12000, "2026-11-10")
    await lancar(real_client, auth_headers, carteira, "expense", 4590, "2026-11-07")

    resposta = await real_client.get(
        URL,
        params={"from": "2026-11-01", "to": "2026-11-30", "account_id": nubank},
        headers=auth_headers,
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["account_id"] == nubank
    assert corpo["opening_balance_cents"] == 700000
    assert corpo["closing_balance_cents"] == 700000 - 12000
    assert [t["amount_cents"] for t in corpo["transactions"]] == [12000]
