from app.users.application.dtos.authenticate_user import AuthenticateUserInput
from app.users.application.use_cases.authenticate_user import (
    AuthenticateUserInteractor,
)
from app.users.domain.entities.user import User
from app.users.domain.value_objects.email import Email
from app.users.domain.value_objects.password import PasswordHash, RawPassword
from tests.users.fakes.authenticate_user_presenter_spy import (
    AuthenticateUserPresenterSpy,
)
from tests.users.fakes.fake_password_hasher import FakePasswordHasher
from tests.users.fakes.fake_token_issuer import FakeTokenIssuer
from tests.users.fakes.fake_unit_of_work import FakeUnitOfWork

SENHA = "S3nha!Forte123"


async def montar(
    hasher: FakePasswordHasher | None = None,
) -> tuple[AuthenticateUserInteractor, AuthenticateUserPresenterSpy, User]:
    uow = FakeUnitOfWork()
    ana = User.register(Email("ana@acme.com"), PasswordHash(f"hash-falso:{SENHA}"))
    await uow.users.add(ana)
    presenter = AuthenticateUserPresenterSpy()
    interactor = AuthenticateUserInteractor(
        uow=uow,
        hasher=hasher or FakePasswordHasher(),
        tokens=FakeTokenIssuer(),
        presenter=presenter,
    )
    return interactor, presenter, ana


async def test_credenciais_certas_recebem_um_token() -> None:
    interactor, presenter, ana = await montar()

    await interactor.execute(
        AuthenticateUserInput(email="ana@acme.com", password=SENHA)
    )

    assert presenter.token is not None
    assert presenter.token.value == f"token-falso:{ana.id.value}"


async def test_senha_errada_e_recusada_sem_token() -> None:
    interactor, presenter, _ = await montar()

    await interactor.execute(AuthenticateUserInput(email="ana@acme.com", password="x"))

    assert presenter.invalid_credentials is True
    assert presenter.token is None


async def test_email_desconhecido_recebe_a_mesma_resposta_da_senha_errada() -> None:
    interactor, presenter, _ = await montar()

    await interactor.execute(
        AuthenticateUserInput(email="ninguem@acme.com", password=SENHA)
    )

    assert presenter.invalid_credentials is True
    assert presenter.token is None


class HasherQueContaOTrabalho(FakePasswordHasher):
    def __init__(self) -> None:
        self.operacoes = 0

    async def hash(self, raw: RawPassword) -> PasswordHash:
        self.operacoes += 1
        return await super().hash(raw)

    async def verify(self, raw: RawPassword, hashed: PasswordHash) -> bool:
        self.operacoes += 1
        return await super().verify(raw, hashed)


async def test_email_desconhecido_custa_o_mesmo_trabalho_que_senha_errada() -> None:
    hasher = HasherQueContaOTrabalho()
    interactor, _, _ = await montar(hasher=hasher)

    await interactor.execute(AuthenticateUserInput(email="ana@acme.com", password="x"))
    com_conta = hasher.operacoes
    await interactor.execute(AuthenticateUserInput(email="bia@acme.com", password="x"))
    sem_conta = hasher.operacoes - com_conta

    assert sem_conta == com_conta == 1


async def test_email_mal_formado_e_so_credencial_invalida() -> None:
    interactor, presenter, _ = await montar()

    await interactor.execute(AuthenticateUserInput(email="nao-e-email", password=SENHA))

    assert presenter.invalid_credentials is True


async def test_senha_vazia_e_so_credencial_invalida() -> None:
    interactor, presenter, _ = await montar()

    await interactor.execute(AuthenticateUserInput(email="ana@acme.com", password=""))

    assert presenter.invalid_credentials is True
