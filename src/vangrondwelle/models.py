from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(slots=True)
class ContactInfo:
    domain: str
    source_url: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    confidence: float = 0.0
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

