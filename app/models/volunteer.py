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

    # ============================================================
    # UPLOADED FILES
    # ============================================================

    passport = Column(String(500))
    qr_code = Column(String(500))
    id_card = Column(String(500))

    # ============================================================
    # PERSONAL INFORMATION
    # ============================================================

    name = Column(String(255), nullable=False)
    phone = Column(String(30), nullable=False)
    gender = Column(String(20))
    age = Column(Integer)

    # ============================================================
    # VOTER INFORMATION
    # ============================================================

    voter_card_number = Column(
        String(100),
        nullable=True,
        index=True,
    )

    # ============================================================
    # LOCATION INFORMATION
    # ============================================================

    # Legacy location fields are retained for exports,
    # membership cards, and existing clients.
    #
    # New registrations are linked to the authoritative
    # Ward and PollingUnit tables below.

    lga = Column(String(100))
    ward = Column(String(100))
    unit = Column(String(100))

    ward_id = Column(
        Integer,
        ForeignKey("wards.id"),
        index=True,
        nullable=True,
    )

    polling_unit_id = Column(
        Integer,
        ForeignKey("polling_units.id"),
        index=True,
        nullable=True,
    )

    ward_location = relationship(
        "Ward",
        back_populates="volunteers",
    )

    polling_unit = relationship(
        "PollingUnit",
        back_populates="volunteers",
    )

    # ============================================================
    # EDUCATION
    # ============================================================

    highest_qualification = Column(String(255))
    additional_qualification = Column(String(255))
    specialization = Column(String(255))

    # ============================================================
    # EMPLOYMENT
    # ============================================================

    employment_status = Column(String(100))

    # ============================================================
    # ACCESSIBILITY
    # ============================================================

    physically_challenged = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    # ============================================================
    # MOVEMENT INFORMATION
    # ============================================================

    aum_member = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    previous_organization = Column(String(255))
    position = Column(String(255))
    expectation = Column(Text)

    # ============================================================
    # TIMESTAMPS
    # ============================================================

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )