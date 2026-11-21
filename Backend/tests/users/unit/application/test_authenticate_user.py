from app.users.application.dtos.authenticate_user import AuthenticateUserInput
from app.users.application.session import hash_refresh_token
from app.users.application.use_cases.authenticate_user import (
    AuthenticateUserInteractor,
)
from app.users.domain.entities.user import User
from app.users.domain.value_objects.email import Email
from app.users.domain.value_objects.password import PasswordHash, RawPassword
from tests.users.fakes.authenticate_user_presenter_spy import (
    AuthenticateUserPresenterSpy,
)
from tests.users.fakes.fake_attempt_guard import fake_attempt_guard
from tests.users.fakes.fake_password_hasher import FakePasswordHasher
from tests.users.fakes.fake_session_issuer import fake_session_issuer
from tests.users.fakes.fake_unit_of_work import FakeUnitOfWork

SENHA = "S3nha!Forte123"


async def montar(
    hasher: FakePasswordHasher | None = None, uow: FakeUnitOfWork | None = None
) -> tuple[AuthenticateUserInteractor, AuthenticateUserPresenterSpy, User]:
    uow = uow or FakeUnitOfWork()
    ana = User.register(Email("ana@acme.com"), PasswordHash(f"hash-falso:{SENHA}"))
    await uow.users.add(ana)
    presenter = AuthenticateUserPresenterSpy()
    interactor = AuthenticateUserInteractor(
        uow=uow,
        hasher=hasher or FakePasswordHasher(),
        issuer=fake_session_issuer(),
        attempts=fake_attempt_guard(),
        presenter=presenter,
    )
    return interactor, presenter, ana


async def test_credenciais_certas_recebem_um_token() -> None:
    interactor, presenter, ana = await montar()

    await interactor.execute(
        AuthenticateUserInput(email="ana@acme.com", password=SENHA)
    )

    assert presenter.session is not None
    assert presenter.session.access_token.value == f"token-falso:{ana.id.value}"
    assert presenter.session.refresh_token == "refresh-falso-1"
    assert presenter.session.refresh_expires_in == 30 * 86400


async def test_senha_errada_e_recusada_sem_token() -> None:
    interactor, presenter, _ = await montar()

    await interactor.execute(AuthenticateUserInput(email="ana@acme.com", password="x"))

    assert presenter.invalid_credentials is True
    assert presenter.session is None


async def test_email_desconhecido_recebe_a_mesma_resposta_da_senha_errada() -> None:
    interactor, presenter, _ = await montar()

    await interactor.execute(
        AuthenticateUserInput(email="ninguem@acme.com", password=SENHA)
    )

    assert presenter.invalid_credentials is True
    assert presenter.session is None


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


async def test_senha_com_byte_nul_e_so_credencial_invalida() -> None:
    interactor, presenter, _ = await montar()

    await interactor.execute(
        AuthenticateUserInput(email="ana@acme.com", password=f"{SENHA}\x00")
    )

    assert presenter.invalid_credentials is True


async def test_login_certo_grava_so_o_hash_do_refresh_token() -> None:
    uow = FakeUnitOfWork()
    interactor, presenter, ana = await montar(uow=uow)

    await interactor.execute(
        AuthenticateUserInput(email="ana@acme.com", password=SENHA)
    )

    assert presenter.session is not None
    [gravado] = uow.refresh_tokens.stored.values()
    assert gravado.user_id == ana.id
    assert gravado.token_hash == hash_refresh_token(presenter.session.refresh_token)
    assert gravado.token_hash != presenter.session.refresh_token
    assert uow.committed is True


async def test_login_recusado_nao_grava_nenhum_refresh_token() -> None:
    uow = FakeUnitOfWork()
    interactor, _, _ = await montar(uow=uow)

    await interactor.execute(AuthenticateUserInput(email="ana@acme.com", password="x"))

    assert uow.refresh_tokens.stored == {}
    assert uow.committed is False
