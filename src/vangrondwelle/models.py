from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(slots=True)
class ContactInfo:
    domain: str
    provider_name: str | None = None
    website_url: str | None = None
    directory_source: str | None = None
    directory_detail_url: str | None = None
    source_url: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    confidence: float = 0.0
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class ProviderSeed:
    provider_name: str
    website_url: str
    domain: str
    directory_source: str
    directory_detail_url: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

