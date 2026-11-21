import uuid
from datetime import date, timedelta

import pytest

from app.finance.application.dtos.transaction_warning import TransactionWarning
from app.finance.application.use_cases.run_due_recurrences import (
    RunDueRecurrencesInteractor,
    RunReport,
)
from app.finance.domain.entities.account import Account
from app.finance.domain.entities.recurrence import Recurrence
from app.finance.domain.entities.transaction import Transaction
from app.finance.domain.exceptions import DuplicateOccurrenceError
from app.finance.domain.value_objects.account_kind import AccountKind
from app.finance.domain.value_objects.account_name import AccountName
from app.finance.domain.value_objects.active_range import ActiveRange
from app.finance.domain.value_objects.category import Category
from app.finance.domain.value_objects.description import Description
from app.finance.domain.value_objects.frequency import Frequency
from app.finance.domain.value_objects.money import Money
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.schedule import Schedule
from app.finance.domain.value_objects.transaction_kind import TransactionKind
from tests.finance.fakes.fake_categorizer import FakeCategorizer
from tests.finance.fakes.fake_recurrence_rules import FakeRecurrenceRules
from tests.finance.fakes.fake_transaction_check import FakeTransactionCheck
from tests.finance.fakes.fake_transaction_repository import FakeTransactionRepository
from tests.finance.fakes.fake_unit_of_work import FakeUnitOfWork

ANA = OwnerId(uuid.uuid4())
BIA = OwnerId(uuid.uuid4())
HOJE = date(2026, 12, 20)


class Relator:
    def __init__(self) -> None:
        self.report: RunReport | None = None

    def present_report(self, report: RunReport) -> None:
        self.report = report


def recorrencia(
    dono: OwnerId,
    conta: Account,
    descricao: str = "Aluguel",
    categoria: str | None = "moradia",
    schedule: Schedule = Schedule(Frequency.MONTHLY, 5),  # noqa: B008
    comeca_em: date = date(2026, 12, 1),
    termina_em: date | None = None,
) -> Recurrence:
    return Recurrence.create(
        owner=dono,
        account=conta.id,
        kind=TransactionKind.EXPENSE,
        amount=Money(150000),
        description=Description(descricao),
        category=None if categoria is None else Category(categoria),
        schedule=schedule,
        window=ActiveRange(comeca_em, termina_em),
    )


async def montar(
    *recorrencias: Recurrence,
    checks: tuple[FakeTransactionCheck, ...] = (),
    categoria: str = "outros",
) -> tuple[RunDueRecurrencesInteractor, FakeUnitOfWork, Relator, FakeCategorizer]:
    uow = FakeUnitOfWork()
    for dono in (ANA, BIA):
        await uow.accounts.add(CONTA[dono])
    for r in recorrencias:
        await uow.recurrences.add(r)
    categorizador = FakeCategorizer(Category(categoria))
    relator = Relator()
    interactor = RunDueRecurrencesInteractor(
        uow_factory=lambda: uow,
        categorizer=categorizador,
        checks=checks,
        rules=FakeRecurrenceRules(),
        presenter=relator,
    )
    return interactor, uow, relator, categorizador


CONTA = {
    ANA: Account.open(ANA, AccountName("Corrente"), AccountKind.CHECKING),
    BIA: Account.open(BIA, AccountName("Corrente"), AccountKind.CHECKING),
}


async def test_lanca_a_ocorrencia_do_dia_com_a_recorrencia_de_origem() -> None:
    regra = recorrencia(ANA, CONTA[ANA])
    interactor, uow, relator, _ = await montar(regra)

    await interactor.execute(HOJE)

    [lancada] = uow.transactions.stored
    assert lancada.occurred_on == date(2026, 12, 5)
    assert lancada.recurrence == regra.id
    assert lancada.owner == ANA
    assert lancada.amount == Money(150000)
    assert lancada.category == Category("moradia")
    assert relator.report == RunReport(
        recurrences=1, created=1, skipped_days=0, failures=0
    )


async def test_atualiza_a_ultima_execucao_e_confirma() -> None:
    regra = recorrencia(ANA, CONTA[ANA])
    interactor, uow, _, _ = await montar(regra)

    await interactor.execute(HOJE)

    [gravada] = uow.recurrences.stored
    assert gravada.last_run_on == HOJE
    assert uow.committed is True


async def test_rodar_duas_vezes_no_mesmo_dia_nao_duplica() -> None:
    interactor, uow, relator, _ = await montar(recorrencia(ANA, CONTA[ANA]))

    await interactor.execute(HOJE)
    await interactor.execute(HOJE)

    assert len(uow.transactions.stored) == 1
    assert relator.report == RunReport(
        recurrences=0, created=0, skipped_days=0, failures=0
    )


async def test_dias_depois_lanca_so_o_que_faltava() -> None:
    interactor, uow, _, _ = await montar(
        recorrencia(ANA, CONTA[ANA], schedule=Schedule(Frequency.WEEKLY, 1))
    )

    await interactor.execute(date(2026, 12, 8))
    await interactor.execute(date(2026, 12, 22))

    assert sorted(t.occurred_on for t in uow.transactions.stored) == [
        date(2026, 12, 7),
        date(2026, 12, 14),
        date(2026, 12, 21),
    ]


async def test_respeita_o_fim_da_recorrencia() -> None:
    regra = recorrencia(
        ANA,
        CONTA[ANA],
        schedule=Schedule(Frequency.WEEKLY, 1),
        termina_em=date(2026, 12, 10),
    )
    interactor, uow, _, _ = await montar(regra)

    await interactor.execute(HOJE)
    await interactor.execute(HOJE + timedelta(days=30))

    assert [t.occurred_on for t in uow.transactions.stored] == [date(2026, 12, 7)]
    assert uow.recurrences.stored[0].last_run_on == date(2026, 12, 10)


async def test_categoria_nula_passa_pelo_categorizador() -> None:
    interactor, uow, _, categorizador = await montar(
        recorrencia(ANA, CONTA[ANA], categoria=None), categoria="mercado"
    )

    await interactor.execute(HOJE)

    assert uow.transactions.stored[0].category == Category("mercado")
    assert len(categorizador.asked) == 1


async def test_categoria_informada_nao_chama_o_categorizador() -> None:
    interactor, _, _, categorizador = await montar(recorrencia(ANA, CONTA[ANA]))

    await interactor.execute(HOJE)

    assert categorizador.asked == []


async def test_as_checks_sao_chamadas_e_os_avisos_nao_impedem_o_lancamento() -> None:
    verificacao = FakeTransactionCheck(TransactionWarning("aviso_de_teste", {"n": 1}))
    interactor, uow, _, _ = await montar(
        recorrencia(ANA, CONTA[ANA]), checks=(verificacao,)
    )

    await interactor.execute(HOJE)

    assert len(verificacao.seen) == 1
    assert verificacao.already_stored == [True]
    assert len(uow.transactions.stored) == 1


async def test_recorrencia_com_conta_invalida_falha_sozinha_e_as_outras_seguem() -> (
    None
):
    sem_conta = Account.open(ANA, AccountName("Sumiu"), AccountKind.WALLET)
    ruim = recorrencia(ANA, sem_conta, "Ruim")
    boa = recorrencia(BIA, CONTA[BIA], "Boa")
    interactor, uow, relator, _ = await montar(ruim, boa)

    await interactor.execute(HOJE)

    assert [t.description.text for t in uow.transactions.stored] == ["Boa"]
    assert relator.report == RunReport(
        recurrences=2, created=1, skipped_days=0, failures=1
    )
    ruim_gravada = next(r for r in uow.recurrences.stored if r.id == ruim.id)
    assert ruim_gravada.last_run_on is None


class TransacoesQueDuplicam(FakeTransactionRepository):
    async def add(self, transaction: Transaction) -> None:
        if transaction.description.text == "Duplica":
            raise DuplicateOccurrenceError
        await super().add(transaction)


async def test_ocorrencia_ja_lancada_por_outra_execucao_conta_como_falha() -> None:
    duplicada = recorrencia(ANA, CONTA[ANA], "Duplica")
    normal = recorrencia(BIA, CONTA[BIA], "Normal")
    interactor, uow, relator, _ = await montar(duplicada, normal)
    uow.transactions = TransacoesQueDuplicam()

    await interactor.execute(HOJE)

    assert [t.description.text for t in uow.transactions.stored] == ["Normal"]
    assert relator.report is not None
    assert relator.report.failures == 1
    assert relator.report.created == 1


async def test_o_limite_de_recuperacao_pula_o_antigo_e_conta_os_dias() -> None:
    regra = recorrencia(
        ANA,
        CONTA[ANA],
        schedule=Schedule(Frequency.MONTHLY, 1),
        comeca_em=date(2026, 1, 1),
    )
    interactor, uow, relator, _ = await montar(regra)

    await interactor.execute(HOJE)

    assert [t.occurred_on for t in uow.transactions.stored] == [
        date(2026, 11, 1),
        date(2026, 12, 1),
    ]
    assert relator.report is not None
    assert relator.report.skipped_days > 0


async def test_lanca_as_de_todas_as_pessoas() -> None:
    interactor, uow, relator, _ = await montar(
        recorrencia(ANA, CONTA[ANA], "Da Ana"), recorrencia(BIA, CONTA[BIA], "Da Bia")
    )

    await interactor.execute(HOJE)

    assert {t.owner for t in uow.transactions.stored} == {ANA, BIA}
    assert relator.report is not None
    assert relator.report.recurrences == 2


@pytest.mark.parametrize("hoje", [date(2026, 11, 30), date(2026, 12, 4)])
async def test_sem_data_vencida_nao_lanca_nada_mas_avanca_a_ultima_execucao(
    hoje: date,
) -> None:
    interactor, uow, relator, _ = await montar(
        recorrencia(ANA, CONTA[ANA], comeca_em=date(2026, 11, 6))
    )

    await interactor.execute(hoje)

    assert uow.transactions.stored == []
    assert relator.report is not None
    assert relator.report.created == 0
    assert uow.recurrences.stored[0].last_run_on == hoje
