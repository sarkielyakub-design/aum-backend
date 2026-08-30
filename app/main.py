from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import (
    APP_DESCRIPTION,
    APP_NAME,
    APP_SHORT_NAME,
    APP_TAGLINE,
    APP_VERSION,
    BACKEND_URL,
    FRONTEND_ORIGINS,
)

from app.db.session import Base, engine
from app.db.migrations import upgrade_location_schema


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

UPLOADS_DIR = BASE_DIR / "uploads"
PASSPORTS_DIR = UPLOADS_DIR / "passports"
CARDS_DIR = UPLOADS_DIR / "cards"
QR_DIR = UPLOADS_DIR / "qr"


# ============================================================
# CREATE DIRECTORIES
# ============================================================

for directory in (
    UPLOADS_DIR,
    PASSPORTS_DIR,
    CARDS_DIR,
    QR_DIR,
):
    directory.mkdir(
        parents=True,
        exist_ok=True,
    )


# ============================================================
# DATABASE MODELS
# ============================================================

# IMPORTANT:
# Import every model before create_all().

from app.models.user import User
from app.models.volunteer import Volunteer
from app.models.location import PollingUnit, Ward


# ============================================================
# DATABASE TABLES
# ============================================================

Base.metadata.create_all(
    bind=engine
)

# Upgrade deployments created before ward/polling-unit support.  Existing
# volunteers remain untouched until an administrator explicitly backfills them.
upgrade_location_schema(engine)


# ============================================================
# DEFAULT ADMIN
# ============================================================

from app.init_admin import create_default_admin

create_default_admin()


# ============================================================
# ROUTERS
# ============================================================

from app.api.routes.auth import router as auth_router
from app.api.routes.volunteer import router as volunteer_router
from app.api.routes.admin import router as admin_router


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
)


# ============================================================
# APPLICATION STATE
# ============================================================

app.state.base_dir = BASE_DIR
app.state.uploads_dir = UPLOADS_DIR
app.state.passports_dir = PASSPORTS_DIR
app.state.cards_dir = CARDS_DIR
app.state.qr_dir = QR_DIR
app.state.backend_url = BACKEND_URL
app.state.frontend_url = (
    FRONTEND_ORIGINS[0]
    if FRONTEND_ORIGINS
    else None
)


# ============================================================
# CORS
# ============================================================

allowed_origins = list(
    FRONTEND_ORIGINS
)


# Production frontend
production_frontend = (
    "https://aumdutes.vercel.app"
)

if production_frontend not in allowed_origins:
    allowed_origins.append(
        production_frontend
    )


# Local development
local_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]

for origin in local_origins:
    if origin not in allowed_origins:
        allowed_origins.append(origin)


app.add_middleware(
    CORSMiddleware,

    allow_origins=allowed_origins,

    # Supports Vercel preview deployments
    allow_origin_regex=r"https://.*\.vercel\.app",

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ============================================================
# STATIC UPLOADS
# ============================================================

# Passport:
# https://aum-backend-production.up.railway.app/uploads/passports/FILE.jpg
#
# Card:
# https://aum-backend-production.up.railway.app/uploads/cards/FILE.pdf
#
# QR:
# https://aum-backend-production.up.railway.app/uploads/qr/FILE.png

app.mount(
    "/uploads",
    StaticFiles(
        directory=str(UPLOADS_DIR),
        check_dir=True,
    ),
    name="uploads",
)


# ============================================================
# ROUTERS
# ============================================================

app.include_router(
    auth_router
)

app.include_router(
    volunteer_router
)

app.include_router(
    admin_router
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "success": True,
        "organization": APP_NAME,
        "short_name": APP_SHORT_NAME,
        "tagline": APP_TAGLINE,
        "message": f"{APP_NAME} API is running.",
        "version": APP_VERSION,
        "backend_url": BACKEND_URL,
        "frontend_url": "https://aumdutes.vercel.app",
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "aum-backend",
        "organization": APP_NAME,
        "backend_url": BACKEND_URL,
    }


# ============================================================
# UPLOADS HEALTH
# ============================================================

@app.get("/uploads-health")
def uploads_health():
    return {
        "success": True,
        "backend_url": BACKEND_URL,

        "uploads_exists": (
            UPLOADS_DIR.exists()
        ),

        "passports_exists": (
            PASSPORTS_DIR.exists()
        ),

        "cards_exists": (
            CARDS_DIR.exists()
        ),

        "qr_exists": (
            QR_DIR.exists()
        ),
    }


# ============================================================
# UPLOADS DEBUG
# ============================================================

@app.get("/uploads-debug")
def uploads_debug():

    def files_in(directory: Path):
        if not directory.exists():
            return []

        return sorted(
            file.name
            for file in directory.iterdir()
            if file.is_file()
        )

    passports = files_in(
        PASSPORTS_DIR
    )

    cards = files_in(
        CARDS_DIR
    )

    qr_codes = files_in(
        QR_DIR
    )

    return {
        "success": True,

        "organization": APP_NAME,

        "backend_url": BACKEND_URL,

        "frontend_url": (
            "https://aumdutes.vercel.app"
        ),

        "passports": passports,

        "cards": cards,

        "qr_codes": qr_codes,

        "counts": {
            "passports": len(passports),
            "cards": len(cards),
            "qr_codes": len(qr_codes),
        },
    }
