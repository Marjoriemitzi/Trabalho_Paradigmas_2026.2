from typing import Protocol

from app.users.application.ports.token_verifier import AuthenticatedUser


class AccessTokenCheck(Protocol):
    """Confere, a cada pedido, o que a assinatura do JWT não garante.

    O usuário do token ainda existe e o token não foi revogado no logout.
    """

    async def is_valid(self, current: AuthenticatedUser) -> bool: ...
