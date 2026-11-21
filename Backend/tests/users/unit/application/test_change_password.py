from app.users.application.dtos.change_password import ChangePasswordInput
from app.users.application.use_cases.change_password import ChangePasswordInteractor
from app.users.domain.entities.user import User
from app.users.domain.value_objects.email import Email
from app.users.domain.value_objects.password import PasswordHash
from app.users.domain.value_objects.user_id import UserId
from tests.users.fakes.change_password_presenter_spy import ChangePasswordPresenterSpy
from tests.users.fakes.fake_password_hasher import FakePasswordHasher
from tests.users.fakes.fake_password_policy import FakePasswordPolicy
from tests.users.fakes.fake_unit_of_work import FakeUnitOfWork

ATUAL = "S3nha!Antiga123"
NOVA = "N0va!SenhaForte"


class PoliticaEspia(FakePasswordPolicy):
    def __init__(self) -> None:
        super().__init__(rejects={"fraca": ["too_short", "no_symbol"]})
        self.chamadas = 0

    def check(self, password: str) -> None:
        self.chamadas += 1
        super().check(password)


async def montar() -> (
    tuple[
        ChangePasswordInteractor,
        FakeUnitOfWork,
        ChangePasswordPresenterSpy,
        PoliticaEspia,
        User,
    ]
):
    uow = FakeUnitOfWork()
    ana = User.register(Email("ana@acme.com"), PasswordHash(f"hash-falso:{ATUAL}"))
    await uow.users.add(ana)
    presenter = ChangePasswordPresenterSpy()
    policy = PoliticaEspia()
    interactor = ChangePasswordInteractor(
        uow=uow, hasher=FakePasswordHasher(), policy=policy, presenter=presenter
    )
    return interactor, uow, presenter, policy, ana


async def test_troca_a_senha_grava_o_hash_novo_e_confirma() -> None:
    interactor, uow, presenter, _, ana = await montar()

    await interactor.execute(
        ChangePasswordInput(user_id=ana.id, current_password=ATUAL, new_password=NOVA)
    )

    assert presenter.changed is True
    assert uow.committed is True
    gravado = uow.users.stored(Email("ana@acme.com"))
    assert gravado is not None
    assert gravado.password_hash == PasswordHash(f"hash-falso:{NOVA}")


async def test_senha_atual_errada_nao_troca_e_nem_consulta_a_politica() -> None:
    interactor, uow, presenter, policy, ana = await montar()

    await interactor.execute(
        ChangePasswordInput(
            user_id=ana.id, current_password="errada", new_password=NOVA
        )
    )

    assert presenter.invalid_current_password is True
    assert presenter.changed is False
    assert policy.chamadas == 0
    assert uow.committed is False


async def test_senha_atual_vazia_conta_como_errada() -> None:
    interactor, _, presenter, _, ana = await montar()

    await interactor.execute(
        ChangePasswordInput(user_id=ana.id, current_password="", new_password=NOVA)
    )

    assert presenter.invalid_current_password is True


async def test_senha_atual_com_byte_nul_conta_como_errada() -> None:
    interactor, _, presenter, _, ana = await montar()

    await interactor.execute(
        ChangePasswordInput(
            user_id=ana.id, current_password=f"{ATUAL}\x00", new_password=NOVA
        )
    )

    assert presenter.invalid_current_password is True


async def test_senha_nova_fraca_e_recusada_com_os_motivos() -> None:
    interactor, uow, presenter, _, ana = await montar()

    await interactor.execute(
        ChangePasswordInput(
            user_id=ana.id, current_password=ATUAL, new_password="fraca"
        )
    )

    assert presenter.weak_password == ["too_short", "no_symbol"]
    assert presenter.changed is False
    assert uow.committed is False
    gravado = uow.users.stored(Email("ana@acme.com"))
    assert gravado is not None
    assert gravado.password_hash == PasswordHash(f"hash-falso:{ATUAL}")


async def test_usuario_que_nao_existe_mais_vai_pelo_caminho_de_nao_encontrado() -> None:
    interactor, uow, presenter, _, _ = await montar()

    await interactor.execute(
        ChangePasswordInput(
            user_id=UserId.new(), current_password=ATUAL, new_password=NOVA
        )
    )

    assert presenter.user_not_found is True
    assert uow.committed is False


def test_as_senhas_do_pedido_nao_aparecem_no_repr() -> None:
    pedido = ChangePasswordInput(
        user_id=UserId.new(), current_password=ATUAL, new_password=NOVA
    )

    assert "S3nha" not in repr(pedido)
    assert "N0va" not in repr(pedido)
