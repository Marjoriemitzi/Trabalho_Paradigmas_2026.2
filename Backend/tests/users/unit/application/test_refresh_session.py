from datetime import timedelta

from app.users.application.dtos.refresh_session import LogoutInput, RefreshSessionInput
from app.users.application.session import hash_refresh_token
from app.users.application.use_cases.logout import LogoutInteractor
from app.users.application.use_cases.refresh_session import RefreshSessionInteractor
from app.users.domain.entities.user import User
from app.users.domain.value_objects.email import Email
from app.users.domain.value_objects.password import PasswordHash
from tests.users.fakes.fake_clock import FakeClock
from tests.users.fakes.fake_session_issuer import fake_session_issuer
from tests.users.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.users.fakes.refresh_session_presenter_spies import (
    LogoutPresenterSpy,
    RefreshSessionPresenterSpy,
)


class Cenario:
    def __init__(self) -> None:
        self.uow = FakeUnitOfWork()
        self.clock = FakeClock()
        self.issuer = fake_session_issuer(self.clock)
        self.ana = User.register(Email("ana@acme.com"), PasswordHash("hash"))

    async def abrir_sessao(self) -> str:
        await self.uow.users.add(self.ana)
        sessao = await self.issuer.issue(self.uow, self.ana)
        return sessao.refresh_token

    async def renovar(self, refresh_token: str) -> RefreshSessionPresenterSpy:
        presenter = RefreshSessionPresenterSpy()
        await RefreshSessionInteractor(
            uow=self.uow, issuer=self.issuer, clock=self.clock, presenter=presenter
        ).execute(RefreshSessionInput(refresh_token=refresh_token))
        return presenter

    async def sair(self, refresh_token: str) -> LogoutPresenterSpy:
        presenter = LogoutPresenterSpy()
        await LogoutInteractor(
            uow=self.uow, clock=self.clock, presenter=presenter
        ).execute(LogoutInput(refresh_token=refresh_token))
        return presenter


async def test_a_rotacao_devolve_um_par_novo_na_mesma_familia() -> None:
    c = Cenario()
    antigo = await c.abrir_sessao()

    resultado = await c.renovar(antigo)

    assert resultado.session is not None
    assert resultado.session.refresh_token != antigo
    assert resultado.session.access_token.value == f"token-falso:{c.ana.id.value}"
    antigo_gravado = await c.uow.refresh_tokens.get_by_hash(hash_refresh_token(antigo))
    novo_gravado = await c.uow.refresh_tokens.get_by_hash(
        hash_refresh_token(resultado.session.refresh_token)
    )
    assert antigo_gravado is not None
    assert novo_gravado is not None
    assert antigo_gravado.used_at == c.clock.now()
    assert novo_gravado.family_id == antigo_gravado.family_id
    assert c.uow.committed is True


async def test_o_token_novo_tambem_pode_ser_renovado() -> None:
    c = Cenario()
    antigo = await c.abrir_sessao()
    primeiro = await c.renovar(antigo)
    assert primeiro.session is not None

    segundo = await c.renovar(primeiro.session.refresh_token)

    assert segundo.session is not None


async def test_o_reuso_revoga_a_familia_inteira() -> None:
    c = Cenario()
    antigo = await c.abrir_sessao()
    novo = await c.renovar(antigo)
    assert novo.session is not None

    reuso = await c.renovar(antigo)
    do_novo = await c.renovar(novo.session.refresh_token)

    assert reuso.invalid is True
    assert reuso.session is None
    assert do_novo.invalid is True
    assert all(t.revoked_at is not None for t in c.uow.refresh_tokens.stored.values())


async def test_token_desconhecido_e_invalido() -> None:
    c = Cenario()
    await c.abrir_sessao()

    assert (await c.renovar("nunca-existiu")).invalid is True


async def test_token_vencido_e_invalido_e_nao_e_marcado_como_usado() -> None:
    c = Cenario()
    antigo = await c.abrir_sessao()
    c.clock.advance(timedelta(days=30, seconds=1))

    resultado = await c.renovar(antigo)

    assert resultado.invalid is True
    gravado = await c.uow.refresh_tokens.get_by_hash(hash_refresh_token(antigo))
    assert gravado is not None
    assert gravado.used_at is None


async def test_token_revogado_e_invalido() -> None:
    c = Cenario()
    antigo = await c.abrir_sessao()
    await c.sair(antigo)

    assert (await c.renovar(antigo)).invalid is True


async def test_logout_revoga_a_sessao_e_o_token_novo_tambem_para_de_valer() -> None:
    c = Cenario()
    antigo = await c.abrir_sessao()
    novo = await c.renovar(antigo)
    assert novo.session is not None

    saida = await c.sair(novo.session.refresh_token)

    assert saida.logged_out is True
    assert (await c.renovar(novo.session.refresh_token)).invalid is True


async def test_logout_e_idempotente_e_aceita_token_desconhecido() -> None:
    c = Cenario()
    antigo = await c.abrir_sessao()

    desconhecido = await c.sair("nunca-existiu")
    primeira = await c.sair(antigo)
    segunda = await c.sair(antigo)

    assert desconhecido.logged_out is primeira.logged_out is segunda.logged_out is True


async def test_a_emissao_apaga_os_tokens_vencidos_ha_mais_de_sete_dias() -> None:
    c = Cenario()
    velho = await c.abrir_sessao()
    c.clock.advance(timedelta(days=38))
    await c.issuer.issue(c.uow, c.ana)

    assert await c.uow.refresh_tokens.get_by_hash(hash_refresh_token(velho)) is None
