"""Lança as transações das recorrências que venceram, de forma idempotente.

    docker compose exec app python -m app.run_due_recurrences [--today AAAA-MM-DD]
    docker compose exec app python -m app.run_due_recurrences --every 3600

Sem `--every`, roda uma vez e sai com código 1 se alguma recorrência falhou. Com
`--every N`, repete a cada N segundos (é o que o serviço `scheduler` do compose faz):
como o comando é idempotente, as execuções extras não fazem nada.
"""

import argparse
import asyncio
import logging
import sys
from collections.abc import Sequence
from datetime import date

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.finance.application.use_cases.run_due_recurrences import RunReport
from app.finance.composition import run_due_recurrences_factory
from app.shared.infrastructure.config.settings import Settings
from app.wiring import build_infra

logger = logging.getLogger(__name__)


class _ReportRecorder:
    def __init__(self) -> None:
        self.report: RunReport | None = None

    def present_report(self, report: RunReport) -> None:
        self.report = report


async def run_once(settings: Settings, today: date | None = None) -> RunReport:
    engine = create_async_engine(settings.database_url.get_secret_value())
    try:
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        infra = build_infra(settings, session_factory)
        recorder = _ReportRecorder()
        factory = run_due_recurrences_factory(
            session_factory, infra.categorizer, infra.checks, infra.recurrence_rules
        )
        await factory(recorder).execute(today or infra.day_clock.today())
    finally:
        await engine.dispose()
    if recorder.report is None:
        raise RuntimeError("O caso de uso terminou sem apresentar o relatório.")
    return recorder.report


def _summary(report: RunReport) -> str:
    return (
        f"Recorrências processadas: {report.recurrences}; transações criadas: "
        f"{report.created}; dias pulados: {report.skipped_days}; "
        f"falhas: {report.failures}"
    )


async def _loop(settings: Settings, every: int) -> None:
    while True:
        try:
            sys.stdout.write(_summary(await run_once(settings)) + "\n")
            sys.stdout.flush()
        except OSError:
            logger.exception("Falha ao processar as recorrências; tenta de novo.")
        await asyncio.sleep(every)


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.run_due_recurrences")
    parser.add_argument("--today", type=date.fromisoformat, default=None)
    parser.add_argument("--every", type=int, default=None, metavar="SEGUNDOS")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    settings = Settings()
    if args.every is not None:
        if args.every <= 0:
            sys.stderr.write("--every precisa ser maior que zero\n")
            return 2
        asyncio.run(_loop(settings, args.every))
        return 0
    report = asyncio.run(run_once(settings, args.today))
    sys.stdout.write(_summary(report) + "\n")
    return 1 if report.failures > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
