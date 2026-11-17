import pytest

from app.finance.domain.entities.account import Account
from app.finance.domain.exceptions import AccountNameTakenError
from app.finance.domain.repositories.account_repository import AccountRepository
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.account_kind import AccountKind
from app.finance.domain.value_objects.account_name import AccountName
from app.finance.domain.value_objects.owner_id import OwnerId


def conta(dono: OwnerId, nome: str, kind: AccountKind = AccountKind.WALLET) -> Account:
    return Account.open(dono, AccountName(nome), kind)


class AccountRepositoryContract:
    @pytest.fixture
    def repository(self) -> AccountRepository:
        raise NotImplementedError

    @pytest.fixture
    def dono(self) -> OwnerId:
        raise NotImplementedError

    @pytest.fixture
    def outro_dono(self) -> OwnerId:
        raise NotImplementedError

    async def test_conta_aberta_aparece_na_lista_do_dono(
        self, repository: AccountRepository, dono: OwnerId
    ) -> None:
        nubank = conta(dono, "Nubank", AccountKind.CHECKING)
        await repository.add(nubank)

        [lida] = await repository.list_by_owner(dono)

        assert lida.id == nubank.id
        assert lida.owner == dono
        assert lida.name == AccountName("Nubank")
        assert lida.kind is AccountKind.CHECKING

    async def test_lista_em_ordem_alfabetica_e_so_as_do_dono(
        self, repository: AccountRepository, dono: OwnerId, outro_dono: OwnerId
    ) -> None:
        for nome in ("Nubank", "carteira", "Itaú"):
            await repository.add(conta(dono, nome))
        await repository.add(conta(outro_dono, "Banco do outro"))

        lidas = await repository.list_by_owner(dono)

        assert [c.name.text for c in lidas] == ["carteira", "Itaú", "Nubank"]

    async def test_get_traz_a_conta_do_dono(
        self, repository: AccountRepository, dono: OwnerId
    ) -> None:
        nubank = conta(dono, "Nubank")
        await repository.add(nubank)

        lida = await repository.get(dono, nubank.id)

        assert lida is not None
        assert lida.name == AccountName("Nubank")

    async def test_get_nao_traz_a_conta_de_outra_pessoa(
        self, repository: AccountRepository, dono: OwnerId, outro_dono: OwnerId
    ) -> None:
        do_outro = conta(outro_dono, "Nubank")
        await repository.add(do_outro)

        assert await repository.get(dono, do_outro.id) is None
        assert await repository.get(dono, AccountId.new()) is None

    async def test_nome_repetido_no_mesmo_dono_e_recusado(
        self, repository: AccountRepository, dono: OwnerId
    ) -> None:
        await repository.add(conta(dono, "Nubank"))

        with pytest.raises(AccountNameTakenError):
            await repository.add(conta(dono, "NUBANK"))

    async def test_donos_diferentes_podem_usar_o_mesmo_nome(
        self, repository: AccountRepository, dono: OwnerId, outro_dono: OwnerId
    ) -> None:
        await repository.add(conta(dono, "Nubank"))
        await repository.add(conta(outro_dono, "Nubank"))

        assert len(await repository.list_by_owner(outro_dono)) == 1
