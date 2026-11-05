"""
Porta para a política de senha.
"""

from typing import Protocol


class PasswordPolicy(Protocol):
    def check(self, password: str) -> None:
        """
        Levanta WeakPasswordError, com os motivos, quando a senha é recusada.
        """
        ...
