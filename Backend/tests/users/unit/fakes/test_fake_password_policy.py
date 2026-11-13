import pytest

from app.users.domain.exceptions import WeakPasswordError
from app.users.domain.services.password_policy import PasswordPolicy
from tests.users.fakes.fake_password_policy import FakePasswordPolicy


def test_aceita_qualquer_senha_por_padrao() -> None:
    FakePasswordPolicy().check("qualquer coisa")


def test_fake_cumpre_a_porta() -> None:
    porta: PasswordPolicy = FakePasswordPolicy()
    assert porta is not None


def test_recusa_a_senha_configurada_com_os_motivos() -> None:
    policy = FakePasswordPolicy(rejects={"123": ["too_short", "no_upper"]})
    with pytest.raises(WeakPasswordError) as erro:
        policy.check("123")
    assert erro.value.reasons == ["too_short", "no_upper"]
