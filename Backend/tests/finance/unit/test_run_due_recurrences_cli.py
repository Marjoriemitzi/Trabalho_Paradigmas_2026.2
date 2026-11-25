import asyncio
import logging
import runpy
import sys
from datetime import date
from types import SimpleNamespace

import pytest
from sqlalchemy.exc import OperationalError

from app import run_due_recurrences as cli
from app.finance.application.use_cases.run_due_recurrences import RunReport
from app.shared.infrastructure.config.settings import Settings

HOJE = date(2026, 12, 20)
SEM_FALHAS = RunReport(recurrences=3, created=2, skipped_days=1, failures=0)
COM_FALHAS = RunReport(recurrences=3, created=1, skipped_days=0, failures=2)


class _PararError(Exception):
    """Interrompe o laço infinito do `_loop` no teste."""


def _fingir_execucao(
    monkeypatch: pytest.MonkeyPatch, relatorio: RunReport
) -> list[date | None]:
    pedidos: list[date | None] = []

    async def run_once(_settings: Settings, today: date | None = None) -> RunReport:
        pedidos.append(today)
        return relatorio

    monkeypatch.setattr(cli, "run_once", run_once)
    return pedidos


def test_resumo_mostra_todos_os_numeros_do_relatorio() -> None:
    assert cli._summary(COM_FALHAS) == (
        "Recorrências processadas: 3; transações criadas: 1; dias pulados: 0; "
        "falhas: 2"
    )


@pytest.mark.parametrize("every", ["0", "-5"])
def test_every_nao_positivo_responde_2_com_erro(
    every: str, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.main(["--every", every]) == 2

    saida = capsys.readouterr()
    assert saida.err == "--every precisa ser maior que zero\n"
    assert saida.out == ""


def test_today_sem_falhas_responde_0_e_imprime_o_resumo(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    pedidos = _fingir_execucao(monkeypatch, SEM_FALHAS)

    assert cli.main(["--today", "2026-12-20"]) == 0

    assert pedidos == [HOJE]
    assert capsys.readouterr().out == cli._summary(SEM_FALHAS) + "\n"


def test_today_com_falhas_responde_1_e_imprime_o_resumo(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _fingir_execucao(monkeypatch, COM_FALHAS)

    assert cli.main(["--today", "2026-12-20"]) == 1

    assert capsys.readouterr().out == cli._summary(COM_FALHAS) + "\n"


def test_sem_today_usa_o_dia_do_relogio(monkeypatch: pytest.MonkeyPatch) -> None:
    pedidos = _fingir_execucao(monkeypatch, SEM_FALHAS)

    assert cli.main([]) == 0

    assert pedidos == [None]


def test_every_positivo_entrega_o_intervalo_ao_laco(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    intervalos: list[int] = []

    async def laco(_settings: Settings, every: int) -> None:
        intervalos.append(every)

    monkeypatch.setattr(cli, "_loop", laco)

    assert cli.main(["--every", "3600"]) == 0
    assert intervalos == [3600]


@pytest.mark.parametrize(
    "erro",
    [OSError("banco fora do ar"), OperationalError("SELECT 1", {}, Exception("x"))],
)
def test_laco_registra_a_falha_e_espera_o_intervalo(
    erro: Exception,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    esperas: list[float] = []

    async def run_once(_settings: Settings, _today: date | None = None) -> RunReport:
        raise erro

    async def sleep(segundos: float) -> None:
        esperas.append(segundos)
        raise _PararError

    monkeypatch.setattr(cli, "run_once", run_once)
    monkeypatch.setattr(asyncio, "sleep", sleep)

    with (
        caplog.at_level(logging.ERROR, logger=cli.__name__),
        pytest.raises(_PararError),
    ):
        asyncio.run(cli._loop(Settings(), 42))

    assert esperas == [42]
    [registro] = [r for r in caplog.records if r.name == cli.__name__]
    assert registro.getMessage() == "Falha ao processar as recorrências; tenta de novo."
    assert registro.exc_info is not None
    assert registro.exc_info[1] is erro


def test_laco_imprime_o_resumo_de_cada_rodada(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _fingir_execucao(monkeypatch, SEM_FALHAS)
    rodadas = 0

    async def sleep(_segundos: float) -> None:
        nonlocal rodadas
        rodadas += 1
        if rodadas == 2:
            raise _PararError

    monkeypatch.setattr(asyncio, "sleep", sleep)

    with pytest.raises(_PararError):
        asyncio.run(cli._loop(Settings(), 1))

    assert capsys.readouterr().out == (cli._summary(SEM_FALHAS) + "\n") * 2


def test_run_once_sem_relatorio_apresentado_e_um_erro_claro(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _Mudo:
        async def execute(self, _today: date) -> None:
            return None

    def fabrica(*_args: object) -> object:
        return lambda _presenter: _Mudo()

    def infra(*_args: object) -> SimpleNamespace:
        return SimpleNamespace(
            categorizer=None, checks=(), recurrence_rules=None, day_clock=None
        )

    monkeypatch.setattr(cli, "build_infra", infra)
    monkeypatch.setattr(cli, "run_due_recurrences_factory", fabrica)

    with pytest.raises(RuntimeError, match="sem apresentar o relatório"):
        asyncio.run(cli.run_once(Settings(), HOJE))


def test_rodar_como_modulo_sai_com_o_codigo_do_main(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["run_due_recurrences", "--every", "0"])

    # Tira o módulo já importado para o runpy executá-lo do zero, sem aviso.
    monkeypatch.delitem(sys.modules, "app.run_due_recurrences", raising=False)
    with pytest.raises(SystemExit) as saida:
        runpy.run_module("app.run_due_recurrences", run_name="__main__")

    assert saida.value.code == 2
    assert "--every precisa ser maior que zero" in capsys.readouterr().err
