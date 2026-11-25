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


async def test_renomear_e_nome_repetido(
    real_client: AsyncClient, auth_headers: dict[str, str], carteira: str
) -> None:
    await real_client.post(
        URL, json={"name": "Nubank", "kind": "checking"}, headers=auth_headers
    )

    renomeada = await real_client.patch(
        f"{URL}/{carteira}", json={"name": "Dinheiro"}, headers=auth_headers
    )
    repetida = await real_client.patch(
        f"{URL}/{carteira}", json={"name": "NUBANK"}, headers=auth_headers
    )
    so_a_caixa = await real_client.patch(
        f"{URL}/{carteira}", json={"name": "DINHEIRO"}, headers=auth_headers
    )

    assert renomeada.status_code == 200
    assert renomeada.json()["name"] == "Dinheiro"
    assert repetida.status_code == 409
    assert so_a_caixa.status_code == 200


async def test_apagar_conta_vazia_ela_some_da_lista(
    real_client: AsyncClient, auth_headers: dict[str, str], carteira: str
) -> None:
    apagada = await real_client.delete(f"{URL}/{carteira}", headers=auth_headers)

    lista = await real_client.get(URL, headers=auth_headers)
    assert apagada.status_code == 204
    assert lista.json() == {"accounts": []}


async def test_conta_com_transacao_nao_pode_ser_apagada(
    real_client: AsyncClient, auth_headers: dict[str, str], carteira: str
) -> None:
    lancamento = {
        "account_id": carteira,
        "kind": "expense",
        "amount_cents": 1500,
        "description": "Lanche",
        "occurred_on": "2026-11-07",
    }
    await real_client.post(
        "/api/v1/transactions", json=lancamento, headers=auth_headers
    )

    resposta = await real_client.delete(f"{URL}/{carteira}", headers=auth_headers)

    assert resposta.status_code == 409
    assert resposta.json() == {"error": "account_in_use"}
    lista = await real_client.get(URL, headers=auth_headers)
    assert [c["name"] for c in lista.json()["accounts"]] == ["Carteira"]


async def test_conta_de_outra_pessoa_responde_404(
    real_client: AsyncClient,
    auth_headers: dict[str, str],
    carteira: str,
    intruso: dict[str, str],
) -> None:
    renomear = await real_client.patch(
        f"{URL}/{carteira}", json={"name": "X"}, headers=intruso
    )
    apagar = await real_client.delete(f"{URL}/{carteira}", headers=intruso)

    assert renomear.status_code == apagar.status_code == 404
    assert apagar.json() == {"error": "account_not_found"}
