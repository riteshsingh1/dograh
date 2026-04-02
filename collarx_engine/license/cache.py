import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


DEFAULT_CACHE_TTL_HOURS = 24
DEFAULT_GRACE_HOURS = 72


@dataclass
class LicenseCacheRecord:
    validated_at: datetime
    valid: bool
    features: list[str]
    expires_at: str | None
    last_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "validated_at": self.validated_at.isoformat(),
            "valid": self.valid,
            "features": self.features,
            "expires_at": self.expires_at,
            "last_error": self.last_error,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "LicenseCacheRecord":
        validated_at = datetime.fromisoformat(payload["validated_at"])
        if validated_at.tzinfo is None:
            validated_at = validated_at.replace(tzinfo=UTC)
        return cls(
            validated_at=validated_at,
            valid=bool(payload.get("valid", False)),
            features=list(payload.get("features", [])),
            expires_at=payload.get("expires_at"),
            last_error=payload.get("last_error"),
        )


class LicenseCache:
    def __init__(self, cache_file: Path, ttl_hours: int = DEFAULT_CACHE_TTL_HOURS) -> None:
        self.cache_file = cache_file
        self.ttl_hours = ttl_hours

    def load(self) -> LicenseCacheRecord | None:
        if not self.cache_file.exists():
            return None
        try:
            data = json.loads(self.cache_file.read_text())
            return LicenseCacheRecord.from_dict(data)
        except Exception:
            return None

    def save(self, record: LicenseCacheRecord) -> None:
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.cache_file.write_text(json.dumps(record.to_dict(), indent=2))

    def is_fresh(self, record: LicenseCacheRecord) -> bool:
        age = datetime.now(UTC) - record.validated_at
        return age <= timedelta(hours=self.ttl_hours)

    def within_grace(self, record: LicenseCacheRecord, grace_hours: int = DEFAULT_GRACE_HOURS) -> bool:
        age = datetime.now(UTC) - record.validated_at
        return age <= timedelta(hours=grace_hours)
