import uuid
from dataclasses import replace

import pytest

from app.finance.application.dtos.create_account import (
    AccountOutput,
    CreateAccountInput,
)
from app.finance.application.use_cases.create_account import CreateAccountInteractor
from app.finance.domain.value_objects.owner_id import OwnerId
from tests.finance.fakes.create_account_presenter_spy import (
    CreateAccountPresenterSpy,
)
from tests.finance.fakes.fake_unit_of_work import FakeUnitOfWork

DONO = uuid.uuid4()
PEDIDO = CreateAccountInput(owner_id=DONO, name="Nubank", kind="checking")


def montar() -> (
    tuple[CreateAccountInteractor, FakeUnitOfWork, CreateAccountPresenterSpy]
):
    uow = FakeUnitOfWork()
    presenter = CreateAccountPresenterSpy()
    return CreateAccountInteractor(uow=uow, presenter=presenter), uow, presenter


async def test_conta_valida_e_gravada_e_apresentada() -> None:
    interactor, uow, presenter = montar()

    await interactor.execute(PEDIDO)

    assert uow.committed is True
    [gravada] = uow.accounts.stored
    assert gravada.owner == OwnerId(DONO)
    assert presenter.created == AccountOutput(
        id=str(gravada.id.value), name="Nubank", kind="checking"
    )


@pytest.mark.parametrize(
    ("recusado", "esperado"),
    [
        (replace(PEDIDO, name="   "), ("name", "blank")),
        (replace(PEDIDO, kind="savings"), ("kind", "unknown")),
    ],
)
async def test_dado_recusado_diz_qual_campo_foi(
    recusado: CreateAccountInput, esperado: tuple[str, str]
) -> None:
    interactor, uow, presenter = montar()

    await interactor.execute(recusado)

    assert presenter.invalid == esperado
    assert uow.accounts.stored == []


async def test_nome_repetido_e_apresentado_como_conflito() -> None:
    interactor, uow, presenter = montar()
    await interactor.execute(PEDIDO)

    await interactor.execute(replace(PEDIDO, name="NUBANK", kind="credit_card"))

    assert presenter.name_taken == "NUBANK"
    assert len(uow.accounts.stored) == 1
