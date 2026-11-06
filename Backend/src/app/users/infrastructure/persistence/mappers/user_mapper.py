from app.users.domain.entities.user import User
from app.users.domain.value_objects.email import Email
from app.users.domain.value_objects.password import PasswordHash
from app.users.domain.value_objects.role import Role
from app.users.domain.value_objects.user_id import UserId
from app.users.infrastructure.persistence.models.user_model import UserModel


def to_model(user: User) -> UserModel:
    return UserModel(
        id=user.id.value,
        email=user.email.value,
        password_hash=user.password_hash.value,
        role=user.role.value,
    )


def to_entity(model: UserModel) -> User:
    return User(
        id=UserId(model.id),
        email=Email(model.email),
        password_hash=PasswordHash(model.password_hash),
        role=Role(model.role),
    )
