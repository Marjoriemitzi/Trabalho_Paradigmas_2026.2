import uuid
from datetime import date

from app.finance.application.dtos.delete_account import DeleteAccountInput
from app.finance.application.use_cases.delete_account import DeleteAccountInteractor
from app.finance.domain.entities.account import Account
from app.finance.domain.exceptions import AccountInUseError
from app.finance.domain.value_objects.account_kind import AccountKind
from app.finance.domain.value_objects.account_name import AccountName
from app.finance.domain.value_objects.owner_id import OwnerId
from tests.finance.contracts.transaction_repository_contract import lancamento
from tests.finance.contracts.transfer_repository_contract import transferir
from tests.finance.fakes.delete_account_presenter_spy import DeleteAccountPresenterSpy
from tests.finance.fakes.fake_account_repository import FakeAccountRepository
from tests.finance.fakes.fake_unit_of_work import FakeUnitOfWork

DONO = OwnerId(uuid.uuid4())
DIA = date(2026, 11, 10)


def conta(nome: str) -> Account:
    return Account.open(DONO, AccountName(nome), AccountKind.WALLET)


def pedido(conta: Account, dono: OwnerId = DONO) -> DeleteAccountInput:
    return DeleteAccountInput(owner_id=dono.value, account_id=conta.id.value)


async def test_apaga_a_conta_vazia() -> None:
    uow = FakeUnitOfWork()
    vazia = conta("Vazia")
    await uow.accounts.add(vazia)
    presenter = DeleteAccountPresenterSpy()

    await DeleteAccountInteractor(uow=uow, presenter=presenter).execute(pedido(vazia))

    assert presenter.deleted is True
    assert uow.committed is True
    assert await uow.accounts.get(DONO, vazia.id) is None


async def test_conta_com_transacao_nao_e_apagada() -> None:
    uow = FakeUnitOfWork()
    usada = conta("Usada")
    await uow.accounts.add(usada)
    await uow.transactions.add(lancamento(DONO, usada.id, DIA))
    presenter = DeleteAccountPresenterSpy()

    await DeleteAccountInteractor(uow=uow, presenter=presenter).execute(pedido(usada))

    assert presenter.in_use is True
    assert presenter.deleted is False
    assert uow.committed is False
    assert await uow.accounts.get(DONO, usada.id) is not None


async def test_conta_com_transferencia_nao_e_apagada() -> None:
    uow = FakeUnitOfWork()
    origem, destino = conta("Origem"), conta("Destino")
    await uow.accounts.add(origem)
    await uow.accounts.add(destino)
    await uow.transfers.add(transferir(DONO, origem.id, destino.id))
    presenter = DeleteAccountPresenterSpy()

    await DeleteAccountInteractor(uow=uow, presenter=presenter).execute(pedido(destino))

    assert presenter.in_use is True


async def test_conta_de_outra_pessoa_da_nao_encontrada() -> None:
    uow = FakeUnitOfWork()
    alheia = conta("Alheia")
    await uow.accounts.add(alheia)
    presenter = DeleteAccountPresenterSpy()

    await DeleteAccountInteractor(uow=uow, presenter=presenter).execute(
        pedido(alheia, dono=OwnerId(uuid.uuid4()))
    )

    assert presenter.not_found is True
    assert await uow.accounts.get(DONO, alheia.id) is not None


class RepositorioQuePerdeACorrida(FakeAccountRepository):
    async def remove(self, account: Account) -> None:
        raise AccountInUseError


async def test_se_o_banco_recusar_por_corrida_tambem_e_conta_em_uso() -> None:
    uow = FakeUnitOfWork()
    uow.accounts = RepositorioQuePerdeACorrida()
    vazia = conta("Vazia")
    await uow.accounts.add(vazia)
    presenter = DeleteAccountPresenterSpy()

    await DeleteAccountInteractor(uow=uow, presenter=presenter).execute(pedido(vazia))

    assert presenter.in_use is True
    assert presenter.deleted is False
    assert uow.committed is False
