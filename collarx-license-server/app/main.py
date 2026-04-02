import os
import secrets
from hashlib import sha256
import hmac
from datetime import UTC, datetime
from enum import StrEnum

import httpx
from fastapi import Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import Boolean, DateTime, Enum, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./licenses.db")
ENVATO_TOKEN = os.getenv("ENVATO_TOKEN", "")
ADMIN_KEY = os.getenv("COLLARX_LICENSE_ADMIN_KEY", "change-me")
ADMIN_USERNAME = os.getenv("COLLARX_LICENSE_ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("COLLARX_LICENSE_ADMIN_PASSWORD", "change-me")
SESSION_SECRET = os.getenv("COLLARX_LICENSE_SESSION_SECRET", "")
LICENSE_SIGNING_SECRET = os.getenv("COLLARX_LICENSE_SIGNING_SECRET", "change-me")


class Base(DeclarativeBase):
    pass


class LicenseStatus(StrEnum):
    active = "active"
    revoked = "revoked"


class License(Base):
    __tablename__ = "licenses"

    license_key: Mapped[str] = mapped_column(String(128), primary_key=True)
    purchase_code: Mapped[str] = mapped_column(String(128), index=True)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[LicenseStatus] = mapped_column(Enum(LicenseStatus), default=LicenseStatus.active)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
    activation_count: Mapped[int] = mapped_column(default=0)
    last_validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    envato_verified: Mapped[bool] = mapped_column(Boolean, default=False)


engine = create_engine(DATABASE_URL, future=True)
Base.metadata.create_all(engine)
templates = Jinja2Templates(directory="app/templates")
app = FastAPI(title="Collarx License Server", version="0.1.0")
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET or secrets.token_urlsafe(32),
    same_site="lax",
    https_only=False,
)


def get_session():
    with Session(engine) as session:
        yield session


def require_admin_key(request: Request) -> None:
    provided = request.headers.get("x-admin-key", "")
    if provided != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin key")


def _safe_equal(left: str, right: str) -> bool:
    return hmac.compare_digest(left.encode("utf-8"), right.encode("utf-8"))


def _hash_text(raw: str) -> str:
    return sha256(raw.encode("utf-8")).hexdigest()


def _require_admin_session(request: Request) -> None:
    if request.session.get("admin_authenticated") is True:
        return
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin login required")


def _verify_admin(request: Request) -> None:
    if request.session.get("admin_authenticated") is True:
        return
    require_admin_key(request)


def _issue_signature(license_key: str, domain: str, valid: bool, issued_at: str) -> str:
    payload = f"{license_key}|{domain}|{int(valid)}|{issued_at}"
    return hmac.new(
        LICENSE_SIGNING_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        sha256,
    ).hexdigest()


class ActivateRequest(BaseModel):
    purchase_code: str = Field(min_length=8)
    domain: str = Field(min_length=3)


class ValidateRequest(BaseModel):
    license_key: str = Field(min_length=8)
    domain: str = Field(min_length=3)
    app_version: str = "0.0.0"


async def verify_envato_purchase_code(purchase_code: str) -> bool:
    if not ENVATO_TOKEN:
        return True
    headers = {"Authorization": f"Bearer {ENVATO_TOKEN}"}
    url = f"https://api.envato.com/v3/market/author/sale?code={purchase_code}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, headers=headers)
        return response.status_code == 200


@app.get("/health")
async def health():
    return {"ok": True}


@app.post("/api/v1/licenses/activate")
async def activate(payload: ActivateRequest, session: Session = Depends(get_session)):
    verified = await verify_envato_purchase_code(payload.purchase_code)
    if not verified:
        raise HTTPException(status_code=400, detail="Invalid purchase code.")

    existing = session.scalar(select(License).where(License.purchase_code == payload.purchase_code))
    if existing:
        if existing.domain and existing.domain != payload.domain:
            raise HTTPException(status_code=409, detail="License already bound to a different domain.")
        existing.domain = payload.domain
        existing.activation_count += 1
        existing.envato_verified = True
        session.add(existing)
        session.commit()
        return {"license_key": existing.license_key, "domain": existing.domain}

    license_key = f"clx_{payload.purchase_code[:8]}_{int(datetime.now(UTC).timestamp())}"
    record = License(
        license_key=license_key,
        purchase_code=payload.purchase_code,
        domain=payload.domain,
        activation_count=1,
        envato_verified=True,
    )
    session.add(record)
    session.commit()
    return {"license_key": license_key, "domain": payload.domain}


@app.post("/api/v1/licenses/validate")
async def validate(payload: ValidateRequest, session: Session = Depends(get_session)):
    record = session.scalar(select(License).where(License.license_key == payload.license_key))
    if not record:
        return {"valid": False, "message": "License key not found."}
    if record.status == LicenseStatus.revoked:
        return {"valid": False, "message": "License revoked."}
    if record.domain and record.domain != payload.domain:
        return {"valid": False, "message": "Domain mismatch."}

    record.last_validated_at = datetime.now(UTC)
    session.add(record)
    session.commit()
    issued_at = datetime.now(UTC).isoformat()
    return {
        "valid": True,
        "features": ["core_engine", "campaigns", "telephony"],
        "expires_at": None,
        "issued_at": issued_at,
        "signature": _issue_signature(
            license_key=payload.license_key,
            domain=payload.domain,
            valid=True,
            issued_at=issued_at,
        ),
    }


@app.get("/api/v1/licenses/status")
async def status(license_key: str, session: Session = Depends(get_session)):
    record = session.scalar(select(License).where(License.license_key == license_key))
    if not record:
        raise HTTPException(status_code=404, detail="License not found.")
    return {
        "license_key": record.license_key,
        "domain": record.domain,
        "status": record.status.value,
        "activation_count": record.activation_count,
        "envato_verified": record.envato_verified,
    }


@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, session: Session = Depends(get_session)):
    try:
        _require_admin_session(request)
    except HTTPException:
        return RedirectResponse(url="/admin/login", status_code=303)
    rows = session.scalars(select(License)).all()
    active = len([r for r in rows if r.status == LicenseStatus.active])
    revoked = len([r for r in rows if r.status == LicenseStatus.revoked])
    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={"licenses": rows, "active": active, "revoked": revoked, "total": len(rows)},
    )


@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="admin_login.html",
        context={"error": None},
    )


@app.post("/admin/login", response_class=HTMLResponse)
async def admin_login(request: Request, username: str = Form(...), password: str = Form(...)):
    if not (_safe_equal(_hash_text(username), _hash_text(ADMIN_USERNAME)) and _safe_equal(_hash_text(password), _hash_text(ADMIN_PASSWORD))):
        return templates.TemplateResponse(
            request=request,
            name="admin_login.html",
            context={"error": "Invalid credentials"},
            status_code=401,
        )

    request.session["admin_authenticated"] = True
    return RedirectResponse(url="/admin", status_code=303)


@app.post("/admin/logout")
async def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/admin/login", status_code=303)


@app.post("/admin/create")
async def admin_create(
    request: Request,
    purchase_code: str = Form(...),
    domain: str = Form(""),
    session: Session = Depends(get_session),
):
    _verify_admin(request)
    existing = session.scalar(select(License).where(License.purchase_code == purchase_code))
    if existing:
        return RedirectResponse(url="/admin", status_code=303)

    license_key = f"clx_{purchase_code[:8]}_{int(datetime.now(UTC).timestamp())}"
    row = License(
        license_key=license_key,
        purchase_code=purchase_code,
        domain=domain or None,
        envato_verified=True,
    )
    session.add(row)
    session.commit()
    return RedirectResponse(url="/admin", status_code=303)


@app.post("/admin/revoke")
async def admin_revoke(
    request: Request,
    license_key: str = Form(...),
    session: Session = Depends(get_session),
):
    _verify_admin(request)
    record = session.scalar(select(License).where(License.license_key == license_key))
    if record:
        record.status = LicenseStatus.revoked
        session.add(record)
        session.commit()
    return RedirectResponse(url="/admin", status_code=303)
