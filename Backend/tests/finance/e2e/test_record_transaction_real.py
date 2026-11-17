from httpx import AsyncClient


async def test_lancamento_sem_categoria_e_categorizado_pelo_prolog(
    real_client: AsyncClient, auth_headers: dict[str, str], carteira: str
) -> None:
    resposta = await real_client.post(
        "/api/v1/transactions",
        json={
            "account_id": carteira,
            "kind": "expense",
            "amount_cents": 2390,
            "description": "Uber para o trabalho",
            "occurred_on": "2026-11-07",
        },
        headers=auth_headers,
    )

    assert resposta.status_code == 201
    assert resposta.json()["category"] == "transporte"
    assert resposta.json()["account_id"] == carteira


async def test_categoria_fora_da_lista_e_recusada(
    real_client: AsyncClient, auth_headers: dict[str, str], carteira: str
) -> None:
    resposta = await real_client.post(
        "/api/v1/transactions",
        json={
            "account_id": carteira,
            "kind": "expense",
            "amount_cents": 12000,
            "description": "Mensalidade",
            "occurred_on": "2026-11-08",
            "category": "academia",
        },
        headers=auth_headers,
    )

    assert resposta.status_code == 422
    assert resposta.json() == {
        "error": "invalid_transaction",
        "fields": [{"field": "category", "problem": "not_found"}],
    }
