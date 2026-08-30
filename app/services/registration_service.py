from sqlalchemy.orm import Session

from app.config import REGISTRATION_PREFIX
from app.models.volunteer import Volunteer


def generate_registration_no(db: Session) -> str:
    """Generate the next AUM volunteer registration number."""
    last = (
        db.query(Volunteer)
        .order_by(Volunteer.id.desc())
        .first()
    )

    next_id = (last.id + 1) if last else 1
    return f"{REGISTRATION_PREFIX}-{next_id:06d}"
