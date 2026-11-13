from pathlib import Path

from app.shared.infrastructure.prolog.gateway import PrologGateway
from app.users.domain.exceptions import WeakPasswordError


class PrologPasswordPolicy:
    def __init__(self, gateway: PrologGateway, rules_dir: Path) -> None:
        self._prolog = gateway
        self._prolog.consult(rules_dir / "users" / "password_policy.pl")

    def check(self, password: str) -> None:
        if self._prolog.holds("valid_password", password):
            return
        raise WeakPasswordError(self._prolog.values("password_error", password))
