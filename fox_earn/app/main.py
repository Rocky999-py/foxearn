from __future__ import annotations
import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from .config import get_settings
from .database import init_db, SessionLocal
from .settings_store import ensure_defaults, get_int
from .api import auth, users, taps, tasks, referrals, wallet, transactions, leaderboard, admin as admin_api

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("fox_earn")
settings = get_settings()

app = FastAPI(title="FOX EARN API", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)


class MaintenanceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if (path.startswith("/health") or path.startswith("/api/auth")
            or path == "/" or path.startswith("/docs") or path.startswith("/openapi")
            or path.startswith("/assets") or path.startswith("/admin")):
            return await call_next(request)
        db = SessionLocal()
        try:
            if get_int(db, "maintenance_mode", settings.maintenance_mode):
                return JSONResponse(status_code=503, content={"detail": {"message": "Maintenance mode.", "code": "maintenance_mode"}})
        finally:
            db.close()
        return await call_next(request)


app.add_middleware(MaintenanceMiddleware)


@app.on_event("startup")
def startup():
    init_db()
    db = SessionLocal()
    try:
        ensure_defaults(db)
    finally:
        db.close()
    log.info("FOX EARN backend ready. CORS origins: %s", settings.origins)


@app.get("/health")
def health():
    return {"status": "ok", "app": "FOX EARN", "version": "3.0.0"}


# --- API routes (before static mount) ---
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api", tags=["users"])
app.include_router(taps.router, prefix="/api", tags=["taps"])
app.include_router(tasks.router, prefix="/api", tags=["tasks"])
app.include_router(referrals.router, prefix="/api", tags=["referrals"])
app.include_router(wallet.router, prefix="/api", tags=["wallet"])
app.include_router(transactions.router, prefix="/api", tags=["transactions"])
app.include_router(leaderboard.router, prefix="/api", tags=["leaderboard"])
app.include_router(admin_api.router, prefix="/api", tags=["admin"])


# --- Static frontend (mounted LAST) ---
FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"

if FRONTEND_DIR.exists():
    @app.get("/")
    def serve_index():
        return FileResponse(FRONTEND_DIR / "index.html")

    @app.get("/admin/")
    def serve_admin():
        return FileResponse(FRONTEND_DIR / "admin" / "index.html")

    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="frontend-assets")
    log.info("Serving static frontend from %s", FRONTEND_DIR)
else:
    log.warning("Frontend folder not found at %s", FRONTEND_DIR)
