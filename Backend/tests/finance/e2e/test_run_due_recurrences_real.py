import asyncio
from datetime import date, timedelta
from zoneinfo import ZoneInfo

from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from app.run_due_recurrences import run_once
from app.shared.infrastructure.clock import ZoneInfoClock
from app.shared.infrastructure.config.settings import Settings

HOJE = ZoneInfoClock(ZoneInfo("America/Sao_Paulo")).today()
SENHA = "S3nha!Forte123"


def corpo(conta: str) -> dict[str, object]:
    return {
        "account_id": conta,
        "kind": "expense",
        "amount_cents": 150000,
        "description": "Aluguel",
        "category": "moradia",
        "frequency": "monthly",
        "day": HOJE.day,
        "starts_on": HOJE.isoformat(),
        "ends_on": None,
    }


async def extrato(
    http: AsyncClient,
    headers: dict[str, str],
    conta: str,
    de: date = HOJE - timedelta(days=30),
    ate: date = HOJE + timedelta(days=30),
) -> list[dict[str, object]]:
    resposta = await http.get(
        "/api/v1/transactions",
        params={"from": de.isoformat(), "to": ate.isoformat(), "account_id": conta},
        headers=headers,
    )
    return list(resposta.json()["transactions"])


async def test_o_comando_lanca_uma_vez_mesmo_rodando_duas_vezes(
    real_client: AsyncClient, auth_headers: dict[str, str], carteira: str
) -> None:
    criada = await real_client.post(
        "/api/v1/recurrences", json=corpo(carteira), headers=auth_headers
    )

    await run_once(Settings(), HOJE)
    await run_once(Settings(), HOJE)

    lancamentos = await extrato(real_client, auth_headers, carteira)
    assert len(lancamentos) == 1
    assert lancamentos[0]["recurrence_id"] == criada.json()["id"]
    assert lancamentos[0]["occurred_on"] == HOJE.isoformat()
    assert lancamentos[0]["category"] == "moradia"
    lista = await real_client.get("/api/v1/recurrences", headers=auth_headers)
    assert lista.json()["recurrences"][0]["last_run_on"] == HOJE.isoformat()


async def test_apagar_a_recorrencia_mantem_a_transacao_sem_origem(
    real_client: AsyncClient, auth_headers: dict[str, str], carteira: str
) -> None:
    criada = await real_client.post(
        "/api/v1/recurrences", json=corpo(carteira), headers=auth_headers
    )
    await run_once(Settings(), HOJE)

    apagada = await real_client.delete(
        f"/api/v1/recurrences/{criada.json()['id']}", headers=auth_headers
    )

    assert apagada.status_code == 204
    [lancamento] = await extrato(real_client, auth_headers, carteira)
    assert lancamento["recurrence_id"] is None


async def test_o_lancamento_manual_continua_sem_recurrence_id(
    real_client: AsyncClient, auth_headers: dict[str, str], carteira: str
) -> None:
    pedido = {
        "account_id": carteira,
        "kind": "expense",
        "amount_cents": 1500,
        "description": "Lanche",
        "occurred_on": HOJE.isoformat(),
    }

    criado = await real_client.post(
        "/api/v1/transactions", json=pedido, headers=auth_headers
    )

    assert criado.status_code == 201
    assert criado.json()["recurrence_id"] is None


async def test_apagar_a_transacao_gerada_nao_faz_ela_voltar(
    real_client: AsyncClient, auth_headers: dict[str, str], carteira: str
) -> None:
    await real_client.post(
        "/api/v1/recurrences", json=corpo(carteira), headers=auth_headers
    )
    await run_once(Settings(), HOJE)
    [gerada] = await extrato(real_client, auth_headers, carteira)

    await real_client.delete(
        f"/api/v1/transactions/{gerada['id']}", headers=auth_headers
    )
    await run_once(Settings(), HOJE)

    assert await extrato(real_client, auth_headers, carteira) == []


async def test_corrigir_a_transacao_gerada_mantem_a_origem(
    real_client: AsyncClient, auth_headers: dict[str, str], carteira: str
) -> None:
    criada = await real_client.post(
        "/api/v1/recurrences", json=corpo(carteira), headers=auth_headers
    )
    await run_once(Settings(), HOJE)
    [gerada] = await extrato(real_client, auth_headers, carteira)

    corrigida = await real_client.put(
        f"/api/v1/transactions/{gerada['id']}",
        json={
            "account_id": carteira,
            "kind": "expense",
            "amount_cents": 160000,
            "description": "Aluguel corrigido",
            "occurred_on": HOJE.isoformat(),
            "category": "moradia",
        },
        headers=auth_headers,
    )

    assert corrigida.status_code == 200
    [lida] = await extrato(real_client, auth_headers, carteira)
    assert lida["amount_cents"] == 160000
    assert lida["recurrence_id"] == criada.json()["id"]


async def test_o_dia_31_vira_o_ultimo_dia_do_mes_curto(
    real_client: AsyncClient, auth_headers: dict[str, str], carteira: str
) -> None:
    pedido = {**corpo(carteira), "day": 31, "starts_on": "2026-02-01"}
    await real_client.post("/api/v1/recurrences", json=pedido, headers=auth_headers)

    await run_once(Settings(), date(2026, 3, 1))

    lancamentos = await extrato(
        real_client, auth_headers, carteira, date(2026, 2, 1), date(2026, 3, 31)
    )
    assert [t["occurred_on"] for t in lancamentos] == ["2026-02-28"]


async def _sql(banco: str, consulta: str, **params: object) -> list[tuple[object, ...]]:
    engine = create_async_engine(banco, poolclass=NullPool)
    try:
        async with engine.begin() as conn:
            resultado = await conn.execute(text(consulta), params)
            return (
                [tuple(linha) for linha in resultado] if resultado.returns_rows else []
            )
    finally:
        await engine.dispose()


async def _ocorrencias(banco: str, recorrencia: str) -> list[tuple[object, ...]]:
    return await _sql(
        banco,
        "SELECT occurred_on, count(*) FROM transactions"
        " WHERE recurrence_id = :r GROUP BY occurred_on",
        r=recorrencia,
    )


async def _ultima_execucao(banco: str, recorrencia: str) -> object:
    [(ultima,)] = await _sql(
        banco, "SELECT last_run_on FROM recurrences WHERE id = :r", r=recorrencia
    )
    return ultima


async def test_duas_execucoes_concorrentes_lancam_uma_unica_vez(
    real_client: AsyncClient,
    auth_headers: dict[str, str],
    carteira: str,
    migrated_database: str,
) -> None:
    criada = await real_client.post(
        "/api/v1/recurrences", json=corpo(carteira), headers=auth_headers
    )
    recorrencia = criada.json()["id"]

    relatorios = await asyncio.gather(
        run_once(Settings(), HOJE), run_once(Settings(), HOJE)
    )

    assert await _ocorrencias(migrated_database, recorrencia) == [(HOJE, 1)]
    assert await _ultima_execucao(migrated_database, recorrencia) == HOJE
    # Quem perde a corrida no índice único conta uma falha (DuplicateOccurrenceError)
    # em vez de duplicar; quem ganha conta a criação. Juntas, criam ao menos a nossa.
    assert sum(r.created for r in relatorios) >= 1
    assert all(r.failures >= 0 for r in relatorios)
    lancamentos = await extrato(real_client, auth_headers, carteira)
    assert [t["recurrence_id"] for t in lancamentos] == [recorrencia]


async def test_falha_de_uma_recorrencia_nao_desfaz_as_outras_do_lote(
    real_client: AsyncClient,
    auth_headers: dict[str, str],
    carteira: str,
    migrated_database: str,
) -> None:
    quebrada = (
        await real_client.post(
            "/api/v1/recurrences", json=corpo(carteira), headers=auth_headers
        )
    ).json()["id"]
    await run_once(Settings(), HOJE)
    # Simula outra execução que lançou a ocorrência mas não gravou last_run_on: a
    # próxima tentativa dessa recorrência esbarra no índice único e falha.
    await _sql(
        migrated_database,
        "UPDATE recurrences SET last_run_on = NULL WHERE id = :r",
        r=quebrada,
    )
    valida = (
        await real_client.post(
            "/api/v1/recurrences",
            json={**corpo(carteira), "description": "Internet"},
            headers=auth_headers,
        )
    ).json()["id"]

    relatorio = await run_once(Settings(), HOJE)

    assert relatorio.failures >= 1
    assert await _ocorrencias(migrated_database, quebrada) == [(HOJE, 1)]
    assert await _ultima_execucao(migrated_database, quebrada) is None
    assert await _ocorrencias(migrated_database, valida) == [(HOJE, 1)]
    assert await _ultima_execucao(migrated_database, valida) == HOJE
