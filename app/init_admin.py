import os

from sqlalchemy.orm import Session

from app.config import APP_NAME
from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.user import User


def create_default_admin():
    username = os.getenv("ADMIN_USERNAME")
    password = os.getenv("ADMIN_PASSWORD")

    if not username or not password:
        print("ℹ️ ADMIN_USERNAME/ADMIN_PASSWORD not configured; admin creation skipped.")
        return

    db: Session = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == username).first()
        if not admin:
            db.add(User(
                username=username,
                hashed_password=get_password_hash(password),
                role="admin",
            ))
            db.commit()
            print(f"✅ {APP_NAME} default admin created")
        else:
            print(f"✅ {APP_NAME} admin already exists")
    finally:
        db.close()
