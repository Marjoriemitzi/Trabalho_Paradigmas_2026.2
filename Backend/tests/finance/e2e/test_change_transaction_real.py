from httpx import AsyncClient

URL = "/api/v1/transactions"
NOVEMBRO = {"from": "2026-11-01", "to": "2026-11-30"}


async def test_corrigir_e_apagar_mudam_o_extrato(
    real_client: AsyncClient, auth_headers: dict[str, str], carteira: str
) -> None:
    pedido = {
        "account_id": carteira,
        "kind": "expense",
        "amount_cents": 4590,
        "description": "Padaria",
        "occurred_on": "2026-11-07",
    }
    lancada = (await real_client.post(URL, json=pedido, headers=auth_headers)).json()
    url = f"{URL}/{lancada['id']}"

    corrigida = await real_client.put(
        url,
        json={**pedido, "amount_cents": 4950, "description": "Uber"},
        headers=auth_headers,
    )

    assert corrigida.status_code == 200
    assert corrigida.json()["category"] == "transporte"
    extrato = await real_client.get(URL, params=NOVEMBRO, headers=auth_headers)
    assert extrato.json()["expense_cents"] == 4950

    apagada = await real_client.delete(url, headers=auth_headers)

    assert apagada.status_code == 204
    extrato = await real_client.get(URL, params=NOVEMBRO, headers=auth_headers)
    assert extrato.json()["transactions"] == []
    de_novo = await real_client.delete(url, headers=auth_headers)
    assert de_novo.status_code == 404
