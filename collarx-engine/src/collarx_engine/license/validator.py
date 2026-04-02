import os
import hmac
from hashlib import sha256
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

import httpx

from collarx_engine.license.cache import LicenseCache, LicenseCacheRecord


class LicenseError(RuntimeError):
    pass


@dataclass
class LicenseState:
    validated: bool = False
    validated_at: datetime | None = None
    features: list[str] = field(default_factory=list)
    expires_at: str | None = None


_STATE = LicenseState()


def _cache_file() -> Path:
    default_dir = Path.home() / ".collarx"
    cache_dir = Path(os.getenv("COLLARX_LICENSE_CACHE_DIR", str(default_dir)))
    return cache_dir / "license_cache.json"


async def _validate_online(license_key: str, domain: str, server: str, app_version: str) -> dict:
    payload = {
        "license_key": license_key,
        "domain": domain,
        "app_version": app_version,
    }
    url = f"{server.rstrip('/')}/api/v1/licenses/validate"
    async with httpx.AsyncClient(timeout=8.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        return response.json()


def _normalize_host(input_value: str) -> str:
    value = input_value.strip().lower()
    if not value:
        return ""
    if "://" in value:
        parsed = urlparse(value)
        return (parsed.hostname or "").lower()
    # Handles domain:port or plain domain.
    parsed = urlparse(f"http://{value}")
    return (parsed.hostname or value).lower()


def _verify_domain_binding(licensed_domain: str) -> None:
    backend_endpoint = os.getenv("BACKEND_API_ENDPOINT", "")
    if not backend_endpoint:
        return
    target = _normalize_host(licensed_domain)
    actual = _normalize_host(backend_endpoint)
    if not target or not actual:
        return
    allowed_local = {"localhost", "127.0.0.1", "0.0.0.0"}
    if target in allowed_local and actual in allowed_local:
        return
    if target != actual:
        raise LicenseError(
            f"Domain binding mismatch: licensed={target}, backend={actual}."
        )


def _verify_signed_response(payload: dict, license_key: str, domain: str) -> None:
    secret = os.getenv("COLLARX_LICENSE_SIGNING_SECRET", "")
    if not secret:
        return
    signature = payload.get("signature", "")
    issued_at = payload.get("issued_at", "")
    if not signature or not issued_at:
        raise LicenseError("Signed response required but missing signature metadata.")
    raw = f"{license_key}|{domain}|{int(bool(payload.get('valid', False)))}|{issued_at}"
    expected = hmac.new(secret.encode("utf-8"), raw.encode("utf-8"), sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise LicenseError("License response signature verification failed.")


def _verify_runtime_integrity() -> None:
    expected_hash = os.getenv("COLLARX_ENGINE_SELF_HASH", "").strip().lower()
    if not expected_hash:
        return
    base = Path(__file__).resolve().parent
    files = [base / "__init__.py", base / "cache.py", base / "validator.py"]
    digester = sha256()
    for f in files:
        digester.update(f.read_bytes())
    actual_hash = digester.hexdigest()
    if not hmac.compare_digest(actual_hash, expected_hash):
        raise LicenseError("Runtime integrity check failed for collarx_engine.")


async def initialize(
    license_key: str | None = None,
    domain: str | None = None,
    license_server: str | None = None,
    app_version: str | None = None,
) -> None:
    effective_license_key = license_key or os.getenv("COLLARX_LICENSE_KEY", "")
    effective_domain = domain or os.getenv("COLLARX_LICENSED_DOMAIN", "")
    effective_server = license_server or os.getenv(
        "COLLARX_LICENSE_SERVER",
        "https://licenses.collarx.com",
    )
    effective_version = app_version or os.getenv("APP_VERSION", "0.0.0")

    if not effective_license_key:
        raise LicenseError("Missing COLLARX_LICENSE_KEY.")
    if not effective_domain:
        raise LicenseError("Missing COLLARX_LICENSED_DOMAIN.")
    _verify_runtime_integrity()
    _verify_domain_binding(effective_domain)

    cache = LicenseCache(_cache_file())
    cached_record = cache.load()
    if cached_record and cached_record.valid and cache.is_fresh(cached_record):
        _set_state_from_record(cached_record)
        return

    try:
        data = await _validate_online(
            license_key=effective_license_key,
            domain=effective_domain,
            server=effective_server,
            app_version=effective_version,
        )
        _verify_signed_response(data, effective_license_key, effective_domain)
        if not data.get("valid", False):
            raise LicenseError(data.get("message", "License is invalid."))

        record = LicenseCacheRecord(
            validated_at=datetime.now(UTC),
            valid=True,
            features=list(data.get("features", [])),
            expires_at=data.get("expires_at"),
        )
        cache.save(record)
        _set_state_from_record(record)
    except Exception as exc:
        if cached_record and cached_record.valid and cache.within_grace(cached_record):
            _set_state_from_record(cached_record)
            return
        raise LicenseError(f"License validation failed: {exc}") from exc


def _set_state_from_record(record: LicenseCacheRecord) -> None:
    _STATE.validated = record.valid
    _STATE.validated_at = record.validated_at
    _STATE.features = record.features
    _STATE.expires_at = record.expires_at


def validate_or_raise() -> None:
    if not _STATE.validated:
        raise LicenseError("License is not initialized.")


def get_license_state() -> LicenseState:
    return _STATE
