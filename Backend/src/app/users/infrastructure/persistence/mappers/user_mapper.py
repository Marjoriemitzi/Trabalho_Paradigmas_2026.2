from app.users.domain.entities.user import User
from app.users.infrastructure.persistence.models.user_model import UserModel


def to_model(user: User) -> UserModel:
    return UserModel(
        id=user.id.value,
        email=user.email.value,
        password_hash=user.password_hash.value,
        role=user.role.value,
    )
