from httpx import AsyncClient

URL = "/api/v1/accounts"


async def test_abrir_conta_e_ver_na_lista(
    real_client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    criada = await real_client.post(
        URL, json={"name": "Nubank", "kind": "checking"}, headers=auth_headers
    )
    repetida = await real_client.post(
        URL, json={"name": "NUBANK", "kind": "wallet"}, headers=auth_headers
    )

    assert criada.status_code == 201
    assert repetida.status_code == 409
    lista = await real_client.get(URL, headers=auth_headers)
    assert [c["name"] for c in lista.json()["accounts"]] == ["Nubank"]


async def test_o_saldo_de_cada_conta_vem_das_transacoes_dela(
    real_client: AsyncClient, auth_headers: dict[str, str], carteira: str
) -> None:
    nubank = await real_client.post(
        URL, json={"name": "Nubank", "kind": "checking"}, headers=auth_headers
    )
    for conta, kind, cents in (
        (nubank.json()["id"], "income", 520000),
        (nubank.json()["id"], "expense", 4590),
        (carteira, "expense", 2390),
    ):
        pedido = {
            "account_id": conta,
            "kind": kind,
            "amount_cents": cents,
            "description": "Lançamento",
            "occurred_on": "2026-11-07",
        }
        resposta = await real_client.post(
            "/api/v1/transactions", json=pedido, headers=auth_headers
        )
        assert resposta.status_code == 201

    lista = await real_client.get(URL, headers=auth_headers)

    saldos = {c["name"]: c["balance_cents"] for c in lista.json()["accounts"]}
    assert saldos == {"Carteira": -2390, "Nubank": 515410}
