import os
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# APPLICATION
# ============================================================

APP_NAME = os.getenv(
    "APP_NAME",
    "AMB. USMAN MOVEMENT",
)

APP_SHORT_NAME = os.getenv(
    "APP_SHORT_NAME",
    "AUM",
)

APP_TAGLINE = os.getenv(
    "APP_TAGLINE",
    "Together for Progress.",
)

APP_DESCRIPTION = os.getenv(
    "APP_DESCRIPTION",
    (
        "AMB. USMAN MOVEMENT Volunteer Registration "
        "and Membership Management API."
    ),
)

APP_VERSION = os.getenv(
    "APP_VERSION",
    "1.0.0",
)


# ============================================================
# REGISTRATION
# ============================================================

# Used by registration_service.py
#
# Example:
# AUM-000001
# AUM-000002
# AUM-000003
#
REGISTRATION_PREFIX = os.getenv(
    "REGISTRATION_PREFIX",
    "AUM",
)


# ============================================================
# BACKEND
# ============================================================

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "https://aum-backend-production.up.railway.app",
).rstrip("/")


# ============================================================
# FRONTEND
# ============================================================

FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "https://aumdutes.vercel.app",
).rstrip("/")


# ============================================================
# CORS
# ============================================================

_frontend_origins = os.getenv(
    "FRONTEND_ORIGINS",
    (
        "https://aumdutes.vercel.app,"
        "http://localhost:5173,"
        "http://localhost:3000"
    ),
)

FRONTEND_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in _frontend_origins.split(",")
    if origin.strip()
]


# Always include the production frontend.
if FRONTEND_URL not in FRONTEND_ORIGINS:
    FRONTEND_ORIGINS.append(FRONTEND_URL)


# ============================================================
# DATABASE
# ============================================================

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not configured"
    )


# ============================================================
# AUTHENTICATION
# ============================================================

SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY is not configured"
    )

ALGORITHM = os.getenv(
    "ALGORITHM",
    "HS256",
)


# ============================================================
# DEFAULT ADMIN
# ============================================================

ADMIN_USERNAME = os.getenv(
    "ADMIN_USERNAME",
    "admin",
)

ADMIN_PASSWORD = os.getenv(
    "ADMIN_PASSWORD"
)

if not ADMIN_PASSWORD:
    raise RuntimeError(
        "ADMIN_PASSWORD is not configured"
    )