import uuid
from dataclasses import replace
from datetime import date

import pytest

from app.finance.application.dtos.transfers import (
    CreateTransferInput,
    DeleteTransferInput,
    TransferOutput,
)
from app.finance.application.use_cases.create_transfer import CreateTransferInteractor
from app.finance.application.use_cases.delete_transfer import DeleteTransferInteractor
from app.finance.domain.entities.account import Account
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.account_kind import AccountKind
from app.finance.domain.value_objects.account_name import AccountName
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.transfer_id import TransferId
from tests.finance.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.finance.fakes.transfer_presenter_spies import (
    CreateTransferPresenterSpy,
    DeleteTransferPresenterSpy,
)

ANA = uuid.uuid4()
CORRENTE = Account.open(OwnerId(ANA), AccountName("Corrente"), AccountKind.CHECKING)
CARTAO = Account.open(OwnerId(ANA), AccountName("Cartão"), AccountKind.CREDIT_CARD)
DA_BIA = Account.open(OwnerId(uuid.uuid4()), AccountName("Bia"), AccountKind.WALLET)

FATURA = CreateTransferInput(
    owner_id=ANA,
    from_account_id=CORRENTE.id.value,
    to_account_id=CARTAO.id.value,
    amount_cents=150000,
    description="Pagamento da fatura",
    occurred_on=date(2026, 11, 10),
)


async def uow_com_contas() -> FakeUnitOfWork:
    uow = FakeUnitOfWork()
    for conta in (CORRENTE, CARTAO, DA_BIA):
        await uow.accounts.add(conta)
    return uow


async def test_transferencia_valida_e_gravada_e_apresentada() -> None:
    uow = await uow_com_contas()
    presenter = CreateTransferPresenterSpy()

    await CreateTransferInteractor(uow=uow, presenter=presenter).execute(FATURA)

    assert uow.committed is True
    [gravada] = uow.transfers.stored
    assert gravada.owner == OwnerId(ANA)
    assert presenter.created == TransferOutput(
        id=str(gravada.id.value),
        from_account_id=str(CORRENTE.id.value),
        to_account_id=str(CARTAO.id.value),
        amount_cents=150000,
        description="Pagamento da fatura",
        occurred_on="2026-11-10",
    )


@pytest.mark.parametrize(
    ("recusada", "esperado"),
    [
        (replace(FATURA, amount_cents=0), ("amount_cents", "not_positive")),
        (replace(FATURA, description=" "), ("description", "blank")),
        (
            replace(FATURA, to_account_id=CORRENTE.id.value),
            ("to_account_id", "same_account"),
        ),
        (
            replace(FATURA, from_account_id=DA_BIA.id.value),
            ("from_account_id", "not_found"),
        ),
        (
            replace(FATURA, to_account_id=AccountId.new().value),
            ("to_account_id", "not_found"),
        ),
    ],
    ids=["valor", "descricao", "mesma-conta", "origem-alheia", "destino-inexistente"],
)
async def test_transferencia_recusada_diz_o_campo_e_nao_grava(
    recusada: CreateTransferInput, esperado: tuple[str, str]
) -> None:
    uow = await uow_com_contas()
    presenter = CreateTransferPresenterSpy()

    await CreateTransferInteractor(uow=uow, presenter=presenter).execute(recusada)

    assert presenter.invalid == esperado
    assert uow.transfers.stored == []
    assert uow.committed is False


async def test_apagar_tira_a_transferencia() -> None:
    uow = await uow_com_contas()
    await CreateTransferInteractor(
        uow=uow, presenter=CreateTransferPresenterSpy()
    ).execute(FATURA)
    [gravada] = uow.transfers.stored
    presenter = DeleteTransferPresenterSpy()

    await DeleteTransferInteractor(uow=uow, presenter=presenter).execute(
        DeleteTransferInput(owner_id=ANA, transfer_id=gravada.id.value)
    )

    assert presenter.deleted is True
    assert uow.transfers.stored == []


async def test_apagar_a_de_outra_pessoa_responde_nao_encontrada() -> None:
    uow = await uow_com_contas()
    await CreateTransferInteractor(
        uow=uow, presenter=CreateTransferPresenterSpy()
    ).execute(FATURA)
    presenter = DeleteTransferPresenterSpy()

    await DeleteTransferInteractor(uow=uow, presenter=presenter).execute(
        DeleteTransferInput(
            owner_id=uuid.uuid4(), transfer_id=uow.transfers.stored[0].id.value
        )
    )

    assert presenter.not_found is True
    assert len(uow.transfers.stored) == 1


async def test_apagar_a_que_nao_existe_responde_nao_encontrada() -> None:
    presenter = DeleteTransferPresenterSpy()

    await DeleteTransferInteractor(uow=FakeUnitOfWork(), presenter=presenter).execute(
        DeleteTransferInput(owner_id=ANA, transfer_id=TransferId.new().value)
    )

    assert presenter.not_found is True
