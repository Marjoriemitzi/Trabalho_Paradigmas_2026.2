import uuid

from app.users.domain.value_objects.user_id import UserId


def test_new_gera_identidades_diferentes() -> None:
    assert UserId.new() != UserId.new()


def test_dois_ids_com_o_mesmo_uuid_sao_iguais() -> None:
    valor = uuid.UUID("12345678-1234-5678-1234-567812345678")
    assert UserId(valor) == UserId(valor)
