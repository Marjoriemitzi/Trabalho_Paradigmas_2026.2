from httpx import AsyncClient


async def test_a_lista_vem_do_banco(
    real_client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    resposta = await real_client.get("/api/v1/categories", headers=auth_headers)

    assert resposta.status_code == 200
    de_receita = [
        c["name"] for c in resposta.json()["categories"] if c["kind"] == "income"
    ]
    assert de_receita == ["freelance", "outros", "salario"]
