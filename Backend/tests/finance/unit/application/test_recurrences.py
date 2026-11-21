import uuid
from collections.abc import Callable
from dataclasses import replace
from datetime import date

import pytest

from app.finance.application.dtos.recurrences import (
    CreateRecurrenceInput,
    DeleteRecurrenceInput,
    ListRecurrencesInput,
    UpdateRecurrenceInput,
)
from app.finance.application.use_cases.create_recurrence import (
    CreateRecurrenceInteractor,
)
from app.finance.application.use_cases.delete_recurrence import (
    DeleteRecurrenceInteractor,
)
from app.finance.application.use_cases.list_recurrences import (
    ListRecurrencesInteractor,
)
from app.finance.application.use_cases.update_recurrence import (
    UpdateRecurrenceInteractor,
)
from app.finance.domain.entities.account import Account
from app.finance.domain.value_objects.account_kind import AccountKind
from app.finance.domain.value_objects.account_name import AccountName
from app.finance.domain.value_objects.owner_id import OwnerId
from tests.finance.fakes.fake_recurrence_rules import FakeRecurrenceRules
from tests.finance.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.finance.fakes.recurrence_presenter_spies import (
    CreateRecurrencePresenterSpy,
    DeleteRecurrencePresenterSpy,
    ListRecurrencesPresenterSpy,
    UpdateRecurrencePresenterSpy,
)
from tests.shared.fakes.fixed_clock import FixedClock

ANA = uuid.uuid4()
CORRENTE = Account.open(OwnerId(ANA), AccountName("Corrente"), AccountKind.CHECKING)
DA_BIA = Account.open(OwnerId(uuid.uuid4()), AccountName("Bia"), AccountKind.WALLET)
HOJE = date(2026, 11, 20)
ALUGUEL = CreateRecurrenceInput(
    owner_id=ANA,
    account_id=CORRENTE.id.value,
    kind="expense",
    amount_cents=150000,
    description="Aluguel",
    category="moradia",
    frequency="monthly",
    day=5,
    starts_on=date(2026, 12, 1),
    ends_on=None,
)


async def uow_com_contas() -> FakeUnitOfWork:
    uow = FakeUnitOfWork()
    await uow.accounts.add(CORRENTE)
    await uow.accounts.add(DA_BIA)
    return uow


def criar(
    uow: FakeUnitOfWork,
) -> tuple[CreateRecurrenceInteractor, CreateRecurrencePresenterSpy]:
    presenter = CreateRecurrencePresenterSpy()
    interactor = CreateRecurrenceInteractor(
        uow=uow,
        rules=FakeRecurrenceRules(),
        clock=FixedClock(HOJE),
        presenter=presenter,
    )
    return interactor, presenter


async def criada(
    uow: FakeUnitOfWork, entrada: CreateRecurrenceInput = ALUGUEL
) -> uuid.UUID:
    interactor, presenter = criar(uow)
    await interactor.execute(entrada)
    assert presenter.created is not None
    return uuid.UUID(presenter.created.id)


async def test_criar_grava_e_apresenta_com_a_proxima_data() -> None:
    uow = await uow_com_contas()
    interactor, presenter = criar(uow)

    await interactor.execute(ALUGUEL)

    assert uow.committed is True
    [gravada] = uow.recurrences.stored
    assert gravada.owner == OwnerId(ANA)
    assert presenter.created is not None
    assert presenter.created.id == str(gravada.id.value)
    assert presenter.created.category == "moradia"
    assert presenter.created.next_occurrence_on == "2026-12-05"


async def test_sem_categoria_a_resposta_mostra_null() -> None:
    uow = await uow_com_contas()
    interactor, presenter = criar(uow)

    await interactor.execute(replace(ALUGUEL, category=None))

    assert presenter.created is not None
    assert presenter.created.category is None


@pytest.mark.parametrize(
    ("mudar", "esperado"),
    [
        (lambda c: replace(c, kind="x"), ("kind", "unknown")),
        (lambda c: replace(c, amount_cents=0), ("amount_cents", "not_positive")),
        (lambda c: replace(c, description=" "), ("description", "blank")),
        (lambda c: replace(c, category="Inválida!"), ("category", "invalid_format")),
        (lambda c: replace(c, frequency="yearly"), ("frequency", "unknown")),
        (lambda c: replace(c, day=32), ("day", "out_of_range")),
        (lambda c: replace(c, frequency="weekly", day=8), ("day", "out_of_range")),
        (
            lambda c: replace(c, ends_on=date(2026, 11, 30)),
            ("ends_on", "end_before_start"),
        ),
        (lambda c: replace(c, account_id=DA_BIA.id.value), ("account_id", "not_found")),
        (lambda c: replace(c, account_id=uuid.uuid4()), ("account_id", "not_found")),
        (lambda c: replace(c, kind="income"), ("category", "not_found")),
    ],
)
async def test_dado_recusado_diz_o_campo_e_nao_grava(
    mudar: Callable[[CreateRecurrenceInput], CreateRecurrenceInput],
    esperado: tuple[str, str],
) -> None:
    uow = await uow_com_contas()
    interactor, presenter = criar(uow)

    await interactor.execute(mudar(ALUGUEL))

    assert presenter.invalid == esperado
    assert uow.recurrences.stored == []
    assert uow.committed is False


def atualizar(
    uow: FakeUnitOfWork,
) -> tuple[UpdateRecurrenceInteractor, UpdateRecurrencePresenterSpy]:
    presenter = UpdateRecurrencePresenterSpy()
    interactor = UpdateRecurrenceInteractor(
        uow=uow,
        rules=FakeRecurrenceRules(),
        clock=FixedClock(HOJE),
        presenter=presenter,
    )
    return interactor, presenter


def correcao(recorrencia_id: uuid.UUID, dono: uuid.UUID = ANA) -> UpdateRecurrenceInput:
    return UpdateRecurrenceInput(
        owner_id=dono,
        recurrence_id=recorrencia_id,
        account_id=CORRENTE.id.value,
        kind="expense",
        amount_cents=160000,
        description="Aluguel reajustado",
        category="moradia",
        frequency="weekly",
        day=1,
        starts_on=date(2026, 11, 1),
        ends_on=None,
    )


async def test_corrigir_troca_a_regra_inteira_e_recalcula_a_proxima_data() -> None:
    uow = await uow_com_contas()
    recorrencia_id = await criada(uow)
    interactor, presenter = atualizar(uow)

    await interactor.execute(correcao(recorrencia_id))

    assert presenter.updated is not None
    assert presenter.updated.amount_cents == 160000
    assert presenter.updated.frequency == "weekly"
    assert presenter.updated.next_occurrence_on == "2026-11-23"
    [gravada] = uow.recurrences.stored
    assert gravada.amount.cents == 160000


async def test_corrigir_com_dado_recusado_nao_muda_nada() -> None:
    uow = await uow_com_contas()
    recorrencia_id = await criada(uow)
    interactor, presenter = atualizar(uow)

    await interactor.execute(replace(correcao(recorrencia_id), day=9))

    assert presenter.invalid == ("day", "out_of_range")
    [gravada] = uow.recurrences.stored
    assert gravada.amount.cents == 150000


async def test_corrigir_para_conta_de_outra_pessoa_e_recusado() -> None:
    uow = await uow_com_contas()
    recorrencia_id = await criada(uow)
    interactor, presenter = atualizar(uow)

    await interactor.execute(
        replace(correcao(recorrencia_id), account_id=DA_BIA.id.value)
    )

    assert presenter.invalid == ("account_id", "not_found")


async def test_corrigir_a_de_outra_pessoa_ou_inexistente_da_nao_encontrada() -> None:
    uow = await uow_com_contas()
    recorrencia_id = await criada(uow)
    de_outra_pessoa, inexistente = atualizar(uow), atualizar(uow)

    await de_outra_pessoa[0].execute(correcao(recorrencia_id, dono=uuid.uuid4()))
    await inexistente[0].execute(correcao(uuid.uuid4()))

    assert de_outra_pessoa[1].not_found is True
    assert inexistente[1].not_found is True


async def test_apagar_remove_a_regra() -> None:
    uow = await uow_com_contas()
    recorrencia_id = await criada(uow)
    presenter = DeleteRecurrencePresenterSpy()

    await DeleteRecurrenceInteractor(uow=uow, presenter=presenter).execute(
        DeleteRecurrenceInput(owner_id=ANA, recurrence_id=recorrencia_id)
    )

    assert presenter.deleted is True
    assert uow.recurrences.stored == []


async def test_apagar_a_de_outra_pessoa_ou_inexistente_da_nao_encontrada() -> None:
    uow = await uow_com_contas()
    recorrencia_id = await criada(uow)
    alheia, inexistente = DeleteRecurrencePresenterSpy(), DeleteRecurrencePresenterSpy()

    await DeleteRecurrenceInteractor(uow=uow, presenter=alheia).execute(
        DeleteRecurrenceInput(owner_id=uuid.uuid4(), recurrence_id=recorrencia_id)
    )
    await DeleteRecurrenceInteractor(uow=uow, presenter=inexistente).execute(
        DeleteRecurrenceInput(owner_id=ANA, recurrence_id=uuid.uuid4())
    )

    assert alheia.not_found is inexistente.not_found is True
    assert len(uow.recurrences.stored) == 1


async def test_listar_calcula_a_proxima_data_com_o_relogio_e_ordena() -> None:
    uow = await uow_com_contas()
    await criada(uow)
    await criada(
        uow,
        replace(
            ALUGUEL,
            description="Academia",
            day=21,
            starts_on=date(2026, 1, 1),
        ),
    )
    await criada(
        uow,
        replace(
            ALUGUEL,
            description="Antiga",
            starts_on=date(2026, 1, 1),
            ends_on=date(2026, 6, 30),
        ),
    )
    presenter = ListRecurrencesPresenterSpy()

    await ListRecurrencesInteractor(
        uow=uow,
        rules=FakeRecurrenceRules(),
        clock=FixedClock(HOJE),
        presenter=presenter,
    ).execute(ListRecurrencesInput(owner_id=ANA))

    assert presenter.listed is not None
    assert [(r.description, r.next_occurrence_on) for r in presenter.listed] == [
        ("Academia", "2026-11-21"),
        ("Aluguel", "2026-12-05"),
        ("Antiga", None),
    ]


async def test_listar_traz_so_as_da_pessoa() -> None:
    uow = await uow_com_contas()
    await criada(uow)
    presenter = ListRecurrencesPresenterSpy()

    await ListRecurrencesInteractor(
        uow=uow,
        rules=FakeRecurrenceRules(),
        clock=FixedClock(HOJE),
        presenter=presenter,
    ).execute(ListRecurrencesInput(owner_id=uuid.uuid4()))

    assert presenter.listed == []
