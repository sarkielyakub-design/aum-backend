from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.session import Base


class Ward(Base):
    __tablename__ = "wards"
    __table_args__ = (UniqueConstraint("lga", "name", name="uq_wards_lga_name"),)

    id = Column(Integer, primary_key=True, index=True)
    state = Column(String(100), nullable=True)
    lga = Column(String(100), nullable=False, index=True)
    name = Column(String(100), nullable=False)

    polling_units = relationship(
        "PollingUnit", back_populates="ward", cascade="all, delete-orphan"
    )
    volunteers = relationship("Volunteer", back_populates="ward_location")


class PollingUnit(Base):
    __tablename__ = "polling_units"

    id = Column(Integer, primary_key=True, index=True)
    ward_id = Column(Integer, ForeignKey("wards.id"), nullable=False, index=True)
    code = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    sequence_no = Column(Integer, nullable=True)
    target_members = Column(Integer, nullable=False, default=200)

    ward = relationship("Ward", back_populates="polling_units")
    volunteers = relationship("Volunteer", back_populates="polling_unit")
