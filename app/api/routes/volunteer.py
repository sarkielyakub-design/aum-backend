from __future__ import annotations

import os
import traceback
from io import BytesIO
from pathlib import Path
from typing import Optional

import qrcode
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.responses import FileResponse
from PIL import Image, ImageOps
from pillow_heif import register_heif_opener
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.config import BACKEND_URL
from app.db.session import get_db
from app.models.volunteer import Volunteer
from app.models.location import PollingUnit, Ward
from app.services.registration_service import generate_registration_no
from app.utils.membership_card_generator import generate_membership_card


# ============================================================
# HEIC / HEIF SUPPORT
# ============================================================

register_heif_opener()


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/volunteers",
    tags=["AUM Volunteers"],
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[3]

UPLOADS_DIR = BASE_DIR / "uploads"

PASSPORTS_DIR = UPLOADS_DIR / "passports"
QR_DIR = UPLOADS_DIR / "qr"
CARDS_DIR = UPLOADS_DIR / "cards"


# ============================================================
# CREATE DIRECTORIES
# ============================================================

for directory in (
    PASSPORTS_DIR,
    QR_DIR,
    CARDS_DIR,
):
    directory.mkdir(
        parents=True,
        exist_ok=True,
    )


# ============================================================
# ORGANIZATION
# ============================================================

ORGANIZATION_NAME = "AMB. USMAN MOVEMENT"
ORGANIZATION_SHORT_NAME = "AUM"
ORGANIZATION_TAGLINE = "Together for Progress."


# ============================================================
# PUBLIC UPLOAD URL
# ============================================================

def public_upload_url(
    relative_path: Optional[str],
):
    """
    Convert an internal upload path into a public URL.

    Example:

        uploads/passports/AUM-000001.jpg

    becomes:

        https://backend-url/uploads/passports/AUM-000001.jpg
    """

    if not relative_path:
        return None

    backend_url = (
        BACKEND_URL or ""
    ).rstrip("/")

    return (
        f"{backend_url}/"
        f"{relative_path.lstrip('/')}"
    )


# ============================================================
# RELATIVE PATH
# ============================================================

def relative_path(
    path: str | Path,
):
    """
    Convert an absolute filesystem path into
    a project-relative path.
    """

    return os.path.relpath(
        os.path.abspath(path),
        BASE_DIR,
    )


# ============================================================
# CLEANUP FILES
# ============================================================

def _cleanup(
    paths,
):
    """
    Delete generated files when registration fails.
    """

    for path in paths:

        if not path:
            continue

        absolute = Path(path)

        if not absolute.is_absolute():
            absolute = BASE_DIR / path

        try:

            if absolute.is_file():
                absolute.unlink()

        except OSError:

            pass


def _location_payload(polling_unit: PollingUnit, member_count: int = 0):
    """Return the canonical location values used by registration clients."""
    ward = polling_unit.ward
    return {
        "id": polling_unit.id,
        "code": polling_unit.code,
        "name": polling_unit.name,
        "sequence_no": polling_unit.sequence_no,
        "target_members": polling_unit.target_members,
        "registered_members": member_count,
        "remaining_members": max(polling_unit.target_members - member_count, 0),
        "ward": {"id": ward.id, "name": ward.name, "lga": ward.lga, "state": ward.state},
    }


def _resolve_polling_unit(
    db: Session,
    polling_unit_id: Optional[int],
    lga: str,
    ward: str,
    unit: str,
) -> PollingUnit:
    """Resolve a submitted location, including compatible legacy form fields."""
    query = db.query(PollingUnit).join(Ward)

    if polling_unit_id is not None:
        polling_unit = query.filter(PollingUnit.id == polling_unit_id).first()
        if not polling_unit:
            raise HTTPException(status_code=422, detail="Selected polling unit does not exist.")
        location_ward = polling_unit.ward
        checks = ((lga, location_ward.lga, "LGA"), (ward, location_ward.name, "ward"))
        for submitted, canonical, label in checks:
            if submitted and submitted.strip().casefold() != canonical.casefold():
                raise HTTPException(status_code=422, detail=f"Selected polling unit does not belong to the submitted {label}.")
        if unit and unit.strip().casefold() not in {polling_unit.name.casefold(), polling_unit.code.casefold()}:
            raise HTTPException(status_code=422, detail="Selected polling unit does not match the submitted unit.")
        return polling_unit

    # Existing forms send lga/ward/unit strings. Resolve them only when they
    # exactly match imported data; never create geography from a registration.
    if not all((lga.strip(), ward.strip(), unit.strip())):
        raise HTTPException(status_code=422, detail="A valid ward and polling unit selection is required.")

    polling_unit = (
        query.filter(
            func.lower(Ward.lga) == lga.strip().lower(),
            func.lower(Ward.name) == ward.strip().lower(),
            or_(
                func.lower(PollingUnit.name) == unit.strip().lower(),
                func.lower(PollingUnit.code) == unit.strip().lower(),
            ),
        )
        .first()
    )
    if not polling_unit:
        raise HTTPException(
            status_code=422,
            detail="Polling unit was not found in the imported ward data. Select a listed polling unit.",
        )
    return polling_unit


# ============================================================
# PUBLIC LOCATION LOOKUPS (used by registration forms)
# ============================================================

@router.get("/locations/wards")
def registration_wards(lga: str, db: Session = Depends(get_db)):
    wards = (
        db.query(Ward)
        .filter(func.lower(Ward.lga) == lga.strip().lower())
        .order_by(Ward.name)
        .all()
    )
    return {"lga": lga.strip(), "data": [{"id": item.id, "name": item.name, "state": item.state} for item in wards]}


@router.get("/locations/polling-units")
def registration_polling_units(ward_id: int, db: Session = Depends(get_db)):
    rows = (
        db.query(PollingUnit, func.count(Volunteer.id).label("member_count"))
        .outerjoin(Volunteer, Volunteer.polling_unit_id == PollingUnit.id)
        .filter(PollingUnit.ward_id == ward_id)
        .group_by(PollingUnit.id)
        .order_by(PollingUnit.sequence_no, PollingUnit.code)
        .all()
    )
    return {"ward_id": ward_id, "data": [_location_payload(item, count) for item, count in rows]}


# ============================================================
# REGISTER VOLUNTEER
# ============================================================

@router.post("/register")
async def register_volunteer(

    name: str = Form(...),

    phone: str = Form(...),

    gender: str = Form(...),

    age: int = Form(...),

    lga: str = Form(...),

    ward: str = Form(...),

    unit: str = Form(...),

    polling_unit_id: Optional[int] = Form(None),

    highest_qualification: str = Form(...),

    additional_qualification: Optional[str] = Form(
        None
    ),

    specialization: Optional[str] = Form(
        None
    ),

    employment_status: str = Form(...),

    physically_challenged: bool = Form(
        False
    ),

    aum_member: bool = Form(
        False
    ),

    previous_organization: Optional[str] = Form(
        None
    ),

    position: Optional[str] = Form(
        None
    ),

    expectation: Optional[str] = Form(
        None
    ),

    passport: UploadFile = File(...),

    db: Session = Depends(get_db),
):

    registration_no = None

    passport_path = None

    qr_path = None

    card_path = None

    volunteer = None

    try:

        # Resolve the selection before creating uploads or a member record.
        # This ensures every new registration is assigned to imported geography.
        polling_unit = _resolve_polling_unit(db, polling_unit_id, lga, ward, unit)
        location_ward = polling_unit.ward

        # ====================================================
        # REGISTRATION NUMBER
        # ====================================================

        registration_no = (
            generate_registration_no(db)
        )


        # ====================================================
        # READ PASSPORT
        # ====================================================

        passport_data = (
            await passport.read()
        )

        if not passport_data:

            raise HTTPException(
                status_code=400,
                detail="Passport image is empty.",
            )


        # ====================================================
        # PROCESS PASSPORT
        # ====================================================

        try:

            image = Image.open(
                BytesIO(passport_data)
            )

            image = ImageOps.exif_transpose(
                image
            )

            if image.mode != "RGB":

                image = image.convert(
                    "RGB"
                )

            passport_file = (
                PASSPORTS_DIR
                / f"{registration_no}.jpg"
            )

            image.save(
                passport_file,
                format="JPEG",
                quality=92,
                optimize=True,
            )

            image.close()

            passport_path = relative_path(
                passport_file
            )

        except Exception as exc:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid passport image. "
                    "Upload a valid JPG, PNG, "
                    "HEIC, HEIF or WebP image."
                ),
            ) from exc


        # ====================================================
        # GENERATE QR CODE
        # ====================================================

        qr_file = (
            QR_DIR
            / f"{registration_no}.png"
        )

        verification_url = (
            f"{BACKEND_URL.rstrip('/')}"
            f"/api/volunteers/verify/"
            f"{registration_no}"
        )

        qr = qrcode.make(
            verification_url
        )

        qr.save(
            qr_file
        )

        qr_path = relative_path(
            qr_file
        )


        # ====================================================
        # CREATE VOLUNTEER
        # ====================================================

        volunteer = Volunteer(

            registration_no=registration_no,

            passport=passport_path,

            qr_code=qr_path,

            name=name.strip(),

            phone=phone.strip(),

            gender=gender.strip(),

            age=age,

            lga=location_ward.lga,

            ward=location_ward.name,

            unit=polling_unit.name,

            ward_id=location_ward.id,

            polling_unit_id=polling_unit.id,

            highest_qualification=(
                highest_qualification.strip()
            ),

            additional_qualification=(
                additional_qualification.strip()
                if additional_qualification
                else None
            ),

            specialization=(
                specialization.strip()
                if specialization
                else None
            ),

            employment_status=(
                employment_status.strip()
            ),

            physically_challenged=(
                physically_challenged
            ),

            aum_member=(
                aum_member
            ),

            previous_organization=(
                previous_organization.strip()
                if previous_organization
                else None
            ),

            position=(
                position.strip()
                if position
                else None
            ),

            expectation=(
                expectation.strip()
                if expectation
                else None
            ),
        )


        # ====================================================
        # SAVE VOLUNTEER
        # ====================================================

        db.add(
            volunteer
        )

        db.commit()

        db.refresh(
            volunteer
        )


        # ====================================================
        # GENERATE MEMBERSHIP CARD
        # ====================================================

        card_file = Path(
            generate_membership_card(
                volunteer,
                str(qr_file),
            )
        )

        card_path = relative_path(
            card_file
        )


        # ====================================================
        # SAVE CARD PATH
        # ====================================================

        volunteer.id_card = (
            card_path
        )

        db.commit()

        db.refresh(
            volunteer
        )


        # ====================================================
        # SUCCESS RESPONSE
        # ====================================================

        return {

            "success": True,

            "message": (
                "AUM volunteer registration "
                "successful."
            ),

            "organization": (
                ORGANIZATION_NAME
            ),

            "short_name": (
                ORGANIZATION_SHORT_NAME
            ),

            "tagline": (
                ORGANIZATION_TAGLINE
            ),

            "registration_no": (
                registration_no
            ),

            "volunteer_id": (
                volunteer.id
            ),

            "passport": (
                public_upload_url(
                    passport_path
                )
            ),

            "qr_code": (
                public_upload_url(
                    qr_path
                )
            ),

            "volunteer_card": (
                public_upload_url(
                    card_path
                )
            ),

            "verification_url": (
                verification_url
            ),
        }


    # ========================================================
    # EXPECTED HTTP ERROR
    # ========================================================

    except HTTPException:

        db.rollback()

        _cleanup(
            [
                passport_path,
                qr_path,
                card_path,
            ]
        )

        if (
            volunteer is not None
            and volunteer.id is not None
        ):

            try:

                db.delete(
                    volunteer
                )

                db.commit()

            except Exception:

                db.rollback()

        raise


    # ========================================================
    # UNEXPECTED ERROR
    # ========================================================

    except Exception as exc:

        traceback.print_exc()

        db.rollback()

        _cleanup(
            [
                passport_path,
                qr_path,
                card_path,
            ]
        )

        if (
            volunteer is not None
            and volunteer.id is not None
        ):

            try:

                db.delete(
                    volunteer
                )

                db.commit()

            except Exception:

                db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Volunteer registration failed: "
                f"{exc}"
            ),
        ) from exc


# ============================================================
# GET ALL VOLUNTEERS
# ============================================================

@router.get("/")
def get_all_volunteers(
    db: Session = Depends(get_db),
):

    volunteers = (
        db.query(Volunteer)
        .order_by(
            Volunteer.id.desc()
        )
        .all()
    )

    return {

        "success": True,

        "organization": (
            ORGANIZATION_NAME
        ),

        "count": len(
            volunteers
        ),

        "data": volunteers,
    }


# ============================================================
# STATISTICS
# ============================================================

@router.get("/stats/summary")
def statistics(
    db: Session = Depends(get_db),
):

    return {

        "success": True,

        "organization": (
            ORGANIZATION_NAME
        ),

        "short_name": (
            ORGANIZATION_SHORT_NAME
        ),

        "total_volunteers": (
            db.query(
                Volunteer
            ).count()
        ),

        "male": (
            db.query(Volunteer)
            .filter(
                Volunteer.gender.ilike(
                    "male"
                )
            )
            .count()
        ),

        "female": (
            db.query(Volunteer)
            .filter(
                Volunteer.gender.ilike(
                    "female"
                )
            )
            .count()
        ),

        "employed": (
            db.query(Volunteer)
            .filter(
                Volunteer.employment_status.ilike(
                    "employed"
                )
            )
            .count()
        ),

        "unemployed": (
            db.query(Volunteer)
            .filter(
                Volunteer.employment_status.ilike(
                    "unemployed"
                )
            )
            .count()
        ),

        "physically_challenged": (
            db.query(Volunteer)
            .filter(
                Volunteer.physically_challenged.is_(
                    True
                )
            )
            .count()
        ),

        "aum_members": (
            db.query(Volunteer)
            .filter(
                Volunteer.aum_member.is_(
                    True
                )
            )
            .count()
        ),
    }


# ============================================================
# VERIFY VOLUNTEER
# ============================================================

@router.get(
    "/verify/{registration_no}"
)
def verify_volunteer(
    registration_no: str,
    db: Session = Depends(get_db),
):

    volunteer = (
        db.query(Volunteer)
        .filter(
            Volunteer.registration_no
            == registration_no
        )
        .first()
    )

    if not volunteer:

        raise HTTPException(
            status_code=404,
            detail=(
                "AUM volunteer not found"
            ),
        )

    return {

        "verified": True,

        "organization": (
            ORGANIZATION_NAME
        ),

        "short_name": (
            ORGANIZATION_SHORT_NAME
        ),

        "tagline": (
            ORGANIZATION_TAGLINE
        ),

        "registration_no": (
            volunteer.registration_no
        ),

        "name": volunteer.name,

        "gender": volunteer.gender,

        "age": volunteer.age,

        "phone": volunteer.phone,

        "lga": volunteer.lga,

        "ward": volunteer.ward,

        "unit": volunteer.unit,

        "joined": volunteer.created_at,
    }


# ============================================================
# SEARCH BY REGISTRATION NUMBER
# ============================================================

@router.get(
    "/search/{registration_no}"
)
def search_volunteer(
    registration_no: str,
    db: Session = Depends(get_db),
):

    volunteer = (
        db.query(Volunteer)
        .filter(
            Volunteer.registration_no
            == registration_no
        )
        .first()
    )

    if not volunteer:

        raise HTTPException(
            status_code=404,
            detail=(
                "AUM volunteer not found"
            ),
        )

    return volunteer


# ============================================================
# GET VOLUNTEER BY ID
# ============================================================

@router.get(
    "/{volunteer_id}"
)
def get_volunteer(
    volunteer_id: int,
    db: Session = Depends(get_db),
):

    volunteer = (
        db.query(Volunteer)
        .filter(
            Volunteer.id
            == volunteer_id
        )
        .first()
    )

    if not volunteer:

        raise HTTPException(
            status_code=404,
            detail=(
                "AUM volunteer not found"
            ),
        )

    return volunteer


# ============================================================
# DELETE VOLUNTEER
# ============================================================

@router.delete(
    "/{volunteer_id}"
)
def delete_volunteer(
    volunteer_id: int,
    db: Session = Depends(get_db),
):

    volunteer = (
        db.query(Volunteer)
        .filter(
            Volunteer.id
            == volunteer_id
        )
        .first()
    )

    if not volunteer:

        raise HTTPException(
            status_code=404,
            detail=(
                "AUM volunteer not found"
            ),
        )

    _cleanup(
        [
            volunteer.passport,
            volunteer.qr_code,
            volunteer.id_card,
        ]
    )

    db.delete(
        volunteer
    )

    db.commit()

    return {

        "success": True,

        "message": (
            "AUM volunteer deleted "
            "successfully"
        ),
    }


# ============================================================
# DOWNLOAD VOLUNTEER CARD
# ============================================================

@router.get(
    "/membership-card/{registration_no}"
)
def download_volunteer_card(
    registration_no: str,
    db: Session = Depends(get_db),
):

    volunteer = (
        db.query(Volunteer)
        .filter(
            Volunteer.registration_no
            == registration_no
        )
        .first()
    )

    if not volunteer:

        raise HTTPException(
            status_code=404,
            detail=(
                "AUM volunteer not found"
            ),
        )


    # ========================================================
    # EXISTING CARD
    # ========================================================

    card_path = (
        volunteer.id_card
    )

    absolute = None

    if card_path:

        absolute = (
            BASE_DIR / card_path
            if not os.path.isabs(
                card_path
            )
            else Path(card_path)
        )


    # ========================================================
    # GENERATE CARD IF MISSING
    # ========================================================

    if (
        not absolute
        or not absolute.is_file()
    ):

        qr_path = None

        if volunteer.qr_code:

            qr_path = (
                BASE_DIR
                / volunteer.qr_code
            )


        generated = Path(
            generate_membership_card(
                volunteer,
                str(qr_path)
                if qr_path
                and qr_path.is_file()
                else None,
            )
        )

        volunteer.id_card = (
            relative_path(
                generated
            )
        )

        db.commit()

        absolute = generated


    # ========================================================
    # RETURN PDF
    # ========================================================

    return FileResponse(

        path=str(
            absolute
        ),

        media_type=(
            "application/pdf"
        ),

        filename=(
            f"{registration_no}"
            "-volunteer-card.pdf"
        ),
    )
