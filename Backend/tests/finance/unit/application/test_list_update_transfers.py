import uuid
from collections.abc import Callable
from dataclasses import replace
from datetime import date

import pytest

from app.finance.application.dtos.transfers import (
    CreateTransferInput,
    ListTransfersInput,
    TransferListOutput,
    TransferOutput,
    UpdateTransferInput,
)
from app.finance.application.use_cases.create_transfer import CreateTransferInteractor
from app.finance.application.use_cases.list_transfers import ListTransfersInteractor
from app.finance.application.use_cases.update_transfer import UpdateTransferInteractor
from app.finance.domain.entities.account import Account
from app.finance.domain.value_objects.account_kind import AccountKind
from app.finance.domain.value_objects.account_name import AccountName
from app.finance.domain.value_objects.owner_id import OwnerId
from tests.finance.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.finance.fakes.transfer_presenter_spies import (
    CreateTransferPresenterSpy,
    ListTransfersPresenterSpy,
    UpdateTransferPresenterSpy,
)

ANA = uuid.uuid4()
CORRENTE = Account.open(OwnerId(ANA), AccountName("Corrente"), AccountKind.CHECKING)
CARTAO = Account.open(OwnerId(ANA), AccountName("Cartão"), AccountKind.CREDIT_CARD)
DA_BIA = Account.open(OwnerId(uuid.uuid4()), AccountName("Bia"), AccountKind.WALLET)
NOVEMBRO = ListTransfersInput(
    owner_id=ANA, start=date(2026, 11, 1), end=date(2026, 11, 30)
)


async def montar() -> tuple[FakeUnitOfWork, uuid.UUID]:
    uow = FakeUnitOfWork()
    for conta in (CORRENTE, CARTAO, DA_BIA):
        await uow.accounts.add(conta)
    spy = CreateTransferPresenterSpy()
    await CreateTransferInteractor(uow=uow, presenter=spy).execute(
        CreateTransferInput(
            owner_id=ANA,
            from_account_id=CORRENTE.id.value,
            to_account_id=CARTAO.id.value,
            amount_cents=150000,
            description="Fatura",
            occurred_on=date(2026, 11, 10),
        )
    )
    assert spy.created is not None
    return uow, uuid.UUID(spy.created.id)


def correcao(transfer_id: uuid.UUID) -> UpdateTransferInput:
    return UpdateTransferInput(
        owner_id=ANA,
        transfer_id=transfer_id,
        from_account_id=CORRENTE.id.value,
        to_account_id=CARTAO.id.value,
        amount_cents=160000,
        description="Fatura corrigida",
        occurred_on=date(2026, 11, 11),
    )


async def test_lista_as_do_periodo_com_o_periodo_na_resposta() -> None:
    uow, transfer_id = await montar()
    presenter = ListTransfersPresenterSpy()

    await ListTransfersInteractor(uow=uow, presenter=presenter).execute(NOVEMBRO)

    assert presenter.listed == TransferListOutput(
        start="2026-11-01",
        end="2026-11-30",
        transfers=[
            TransferOutput(
                id=str(transfer_id),
                from_account_id=str(CORRENTE.id.value),
                to_account_id=str(CARTAO.id.value),
                amount_cents=150000,
                description="Fatura",
                occurred_on="2026-11-10",
            )
        ],
    )


@pytest.mark.parametrize(
    ("pedido", "problema"),
    [
        (replace(NOVEMBRO, start=date(2026, 12, 1)), "end_before_start"),
        (replace(NOVEMBRO, end=date(2028, 1, 1)), "too_long"),
    ],
)
async def test_periodo_invalido_e_recusado_no_campo_to(
    pedido: ListTransfersInput, problema: str
) -> None:
    uow, _ = await montar()
    presenter = ListTransfersPresenterSpy()

    await ListTransfersInteractor(uow=uow, presenter=presenter).execute(pedido)

    assert presenter.invalid == ("to", problema)
    assert presenter.listed is None


async def test_nao_lista_as_de_outra_pessoa() -> None:
    uow, _ = await montar()
    presenter = ListTransfersPresenterSpy()

    await ListTransfersInteractor(uow=uow, presenter=presenter).execute(
        replace(NOVEMBRO, owner_id=uuid.uuid4())
    )

    assert presenter.listed is not None
    assert presenter.listed.transfers == []


async def test_corrigir_troca_os_campos_grava_e_apresenta() -> None:
    uow, transfer_id = await montar()
    uow.committed = False
    presenter = UpdateTransferPresenterSpy()

    await UpdateTransferInteractor(uow=uow, presenter=presenter).execute(
        correcao(transfer_id)
    )

    assert uow.committed is True
    assert presenter.updated == TransferOutput(
        id=str(transfer_id),
        from_account_id=str(CORRENTE.id.value),
        to_account_id=str(CARTAO.id.value),
        amount_cents=160000,
        description="Fatura corrigida",
        occurred_on="2026-11-11",
    )
    [gravada] = uow.transfers.stored
    assert gravada.amount.cents == 160000


@pytest.mark.parametrize(
    ("mudar", "esperado"),
    [
        (lambda c: replace(c, amount_cents=0), ("amount_cents", "not_positive")),
        (lambda c: replace(c, description="  "), ("description", "blank")),
        (
            lambda c: replace(c, to_account_id=CORRENTE.id.value),
            ("to_account_id", "same_account"),
        ),
        (
            lambda c: replace(c, to_account_id=DA_BIA.id.value),
            ("to_account_id", "not_found"),
        ),
        (
            lambda c: replace(c, from_account_id=uuid.uuid4()),
            ("from_account_id", "not_found"),
        ),
    ],
)
async def test_correcao_recusada_diz_qual_campo_foi_e_nao_grava(
    mudar: Callable[[UpdateTransferInput], UpdateTransferInput],
    esperado: tuple[str, str],
) -> None:
    uow, transfer_id = await montar()
    uow.committed = False
    presenter = UpdateTransferPresenterSpy()

    await UpdateTransferInteractor(uow=uow, presenter=presenter).execute(
        mudar(correcao(transfer_id))
    )

    assert presenter.invalid == esperado
    assert uow.committed is False
    [gravada] = uow.transfers.stored
    assert gravada.amount.cents == 150000


async def test_corrigir_a_de_outra_pessoa_ou_inexistente_da_nao_encontrada() -> None:
    uow, transfer_id = await montar()
    presenter = UpdateTransferPresenterSpy()

    await UpdateTransferInteractor(uow=uow, presenter=presenter).execute(
        replace(correcao(transfer_id), owner_id=DA_BIA.owner.value)
    )
    outra = UpdateTransferPresenterSpy()
    await UpdateTransferInteractor(uow=uow, presenter=outra).execute(
        correcao(uuid.uuid4())
    )

    assert presenter.not_found is True
    assert outra.not_found is True
