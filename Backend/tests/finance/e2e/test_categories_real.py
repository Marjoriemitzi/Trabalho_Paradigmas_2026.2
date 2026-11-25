from httpx import AsyncClient

CATEGORIAS_ESPERADAS = [
    {"kind": "expense", "name": "lazer", "label": "Lazer"},
    {"kind": "expense", "name": "mercado", "label": "Mercado"},
    {"kind": "expense", "name": "moradia", "label": "Moradia"},
    {"kind": "expense", "name": "outros", "label": "Outros"},
    {"kind": "expense", "name": "saude", "label": "Saúde"},
    {"kind": "expense", "name": "transporte", "label": "Transporte"},
    {"kind": "income", "name": "freelance", "label": "Freelance"},
    {"kind": "income", "name": "outros", "label": "Outros"},
    {"kind": "income", "name": "salario", "label": "Salário"},
]


async def test_a_lista_vem_do_banco_com_as_nove_categorias_e_rotulos(
    real_client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    resposta = await real_client.get("/api/v1/categories", headers=auth_headers)

    assert resposta.status_code == 200
    categorias = resposta.json()["categories"]
    assert sorted(categorias, key=lambda c: (c["kind"], c["name"])) == (
        CATEGORIAS_ESPERADAS
    )
    assert sum(c["kind"] == "expense" for c in categorias) == 6
    assert sum(c["kind"] == "income" for c in categorias) == 3


async def test_a_lista_de_categorias_pode_ficar_em_cache(
    real_client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    resposta = await real_client.get("/api/v1/categories", headers=auth_headers)

    assert resposta.status_code == 200
    assert "no-store" not in resposta.headers.get("cache-control", "")
