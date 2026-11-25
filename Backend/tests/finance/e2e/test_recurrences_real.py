import uuid
from datetime import date

from httpx import AsyncClient

URL = "/api/v1/recurrences"
SENHA = "S3nha!Forte123"


def corpo(conta: str, **muda: object) -> dict[str, object]:
    base: dict[str, object] = {
        "account_id": conta,
        "kind": "expense",
        "amount_cents": 150000,
        "description": "Aluguel",
        "category": "moradia",
        "frequency": "monthly",
        "day": 31,
        "starts_on": "2026-01-01",
        "ends_on": None,
    }
    return {**base, **muda}


async def test_criar_mensal_no_dia_31_e_semanal_e_listar(
    real_client: AsyncClient, auth_headers: dict[str, str], carteira: str
) -> None:
    mensal = await real_client.post(URL, json=corpo(carteira), headers=auth_headers)
    semanal = await real_client.post(
        URL,
        json=corpo(carteira, description="Feira", frequency="weekly", day=1),
        headers=auth_headers,
    )

    lista = await real_client.get(URL, headers=auth_headers)

    assert mensal.status_code == semanal.status_code == 201
    itens = lista.json()["recurrences"]
    assert {r["description"] for r in itens} == {"Aluguel", "Feira"}
    for item in itens:
        proxima = date.fromisoformat(item["next_occurrence_on"])
        assert proxima >= date.today()
        if item["frequency"] == "weekly":
            assert proxima.isoweekday() == 1


async def test_a_proxima_data_do_dia_31_vem_do_prolog(
    real_client: AsyncClient, auth_headers: dict[str, str], carteira: str
) -> None:
    criada = await real_client.post(URL, json=corpo(carteira), headers=auth_headers)

    proxima = date.fromisoformat(criada.json()["next_occurrence_on"])

    assert proxima.day in {28, 29, 30, 31}


async def test_corrigir_e_apagar(
    real_client: AsyncClient, auth_headers: dict[str, str], carteira: str
) -> None:
    criada = await real_client.post(URL, json=corpo(carteira), headers=auth_headers)
    recorrencia = criada.json()["id"]

    corrigida = await real_client.put(
        f"{URL}/{recorrencia}",
        json=corpo(carteira, amount_cents=160000),
        headers=auth_headers,
    )
    apagada = await real_client.delete(f"{URL}/{recorrencia}", headers=auth_headers)
    lista = await real_client.get(URL, headers=auth_headers)

    assert corrigida.status_code == 200
    assert corrigida.json()["amount_cents"] == 160000
    assert apagada.status_code == 204
    assert lista.json() == {"recurrences": []}


async def test_dado_recusado_pelo_banco_e_pelo_dominio(
    real_client: AsyncClient, auth_headers: dict[str, str], carteira: str
) -> None:
    sem_conta = await real_client.post(
        URL, json=corpo(str(uuid.uuid4())), headers=auth_headers
    )
    fim_antes = await real_client.post(
        URL, json=corpo(carteira, ends_on="2025-12-31"), headers=auth_headers
    )
    categoria = await real_client.post(
        URL, json=corpo(carteira, category="salario"), headers=auth_headers
    )

    assert sem_conta.json()["fields"] == [
        {"field": "account_id", "problem": "not_found"}
    ]
    assert fim_antes.json()["fields"] == [
        {"field": "ends_on", "problem": "end_before_start"}
    ]
    assert categoria.json()["fields"] == [{"field": "category", "problem": "not_found"}]


async def test_recorrencia_de_outro_usuario_da_404(
    real_client: AsyncClient,
    auth_headers: dict[str, str],
    carteira: str,
    intruso: dict[str, str],
) -> None:
    criada = await real_client.post(URL, json=corpo(carteira), headers=auth_headers)

    corrigir = await real_client.put(
        f"{URL}/{criada.json()['id']}", json=corpo(carteira), headers=intruso
    )
    apagar = await real_client.delete(f"{URL}/{criada.json()['id']}", headers=intruso)

    assert corrigir.status_code == apagar.status_code == 404
    assert apagar.json() == {"error": "recurrence_not_found"}


async def test_conta_com_recorrencia_nao_pode_ser_apagada(
    real_client: AsyncClient, auth_headers: dict[str, str], carteira: str
) -> None:
    await real_client.post(URL, json=corpo(carteira), headers=auth_headers)

    resposta = await real_client.delete(
        f"/api/v1/accounts/{carteira}", headers=auth_headers
    )

    assert resposta.status_code == 409
    assert resposta.json() == {"error": "account_in_use"}
