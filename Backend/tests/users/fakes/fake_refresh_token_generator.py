class FakeRefreshTokenGenerator:
    def __init__(self) -> None:
        self._count = 0

    def generate(self) -> str:
        self._count += 1
        return f"refresh-falso-{self._count}"
