from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class TransactionWarning:
    code: str
    details: Mapping[str, str | int] = field(default_factory=dict)
