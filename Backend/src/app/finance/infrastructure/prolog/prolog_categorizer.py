import unicodedata
from pathlib import Path

from app.finance.domain.value_objects.category import Category
from app.finance.domain.value_objects.description import Description
from app.finance.domain.value_objects.transaction_kind import TransactionKind
from app.shared.infrastructure.prolog.gateway import PrologGateway


def _sem_acentos_em_minusculas(texto: str) -> str:
    decomposto = unicodedata.normalize("NFKD", texto.lower())
    return "".join(letra for letra in decomposto if not unicodedata.combining(letra))


class PrologCategorizer:
    def __init__(self, gateway: PrologGateway, rules_dir: Path) -> None:
        self._prolog = gateway
        self._prolog.consult(rules_dir / "finance" / "categorization.pl")

    def categorize(self, kind: TransactionKind, description: Description) -> Category:
        texto = _sem_acentos_em_minusculas(description.text)
        [nome] = self._prolog.values("transaction_category", kind.value, texto)
        return Category(nome)
