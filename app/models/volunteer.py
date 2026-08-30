from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class Volunteer(Base):
    __tablename__ = "volunteers"

    id = Column(Integer, primary_key=True, index=True)

    registration_no = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    # Uploaded files
    passport = Column(String(500))
    qr_code = Column(String(500))
    id_card = Column(String(500))

    # Personal information
    name = Column(String(255), nullable=False)
    phone = Column(String(30), nullable=False)
    gender = Column(String(20))
    age = Column(Integer)

    # Legacy location fields are retained for exports, cards, and existing clients.
    # New registrations are linked to the authoritative location tables below.
    lga = Column(String(100))
    ward = Column(String(100))
    unit = Column(String(100))
    ward_id = Column(Integer, ForeignKey("wards.id"), index=True, nullable=True)
    polling_unit_id = Column(
        Integer,
        ForeignKey("polling_units.id"),
        index=True,
        nullable=True,
    )

    ward_location = relationship("Ward", back_populates="volunteers")
    polling_unit = relationship("PollingUnit", back_populates="volunteers")

    # Education
    highest_qualification = Column(String(255))
    additional_qualification = Column(String(255))
    specialization = Column(String(255))

    # Employment
    employment_status = Column(String(100))

    # Optional accessibility information
    physically_challenged = Column(Boolean, default=False, nullable=False)

    # Movement information
    aum_member = Column(Boolean, default=False, nullable=False)
    previous_organization = Column(String(255))
    position = Column(String(255))
    expectation = Column(Text)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
