import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import APP_DESCRIPTION, APP_NAME, APP_SHORT_NAME, APP_TAGLINE, BACKEND_URL
from app.core.dependencies import get_current_admin
from app.core.security import get_password_hash
from app.db.session import get_db
from app.models.user import User
from app.models.volunteer import Volunteer
from app.models.location import PollingUnit, Ward
from app.utils.excel_export import generate_volunteers_excel
from app.utils.pdf_generator import generate_volunteer_report
from app.utils.membership_card_generator import generate_membership_card

router = APIRouter(
    prefix="/api/admin",
    tags=["AUM Administration"],
    dependencies=[Depends(get_current_admin)],
)

BASE_DIR = Path(__file__).resolve().parents[3]


def resolve_file_path(file_path):
    if not file_path:
        return None
    path = Path(str(file_path).strip())
    return path if path.is_absolute() else BASE_DIR / path


registration_open = True


@router.get("/system")
def system_info():
    return {
        "name": APP_NAME,
        "short_name": APP_SHORT_NAME,
        "tagline": APP_TAGLINE,
        "description": APP_DESCRIPTION,
        "version": "1.0.0",
    }


@router.get("/registration-status")
def get_registration_status():
    return {"open": registration_open}


@router.post("/registration-status/toggle")
def toggle_registration_status():
    global registration_open
    registration_open = not registration_open
    return {
        "open": registration_open,
        "message": f"Volunteer registration is now {'open' if registration_open else 'closed'}",
    }


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    total = db.query(Volunteer).count()
    male = db.query(Volunteer).filter(Volunteer.gender.ilike("male")).count()
    female = db.query(Volunteer).filter(Volunteer.gender.ilike("female")).count()
    employed = db.query(Volunteer).filter(Volunteer.employment_status.ilike("employed")).count()
    unemployed = db.query(Volunteer).filter(Volunteer.employment_status.ilike("unemployed")).count()
    aum_members = db.query(Volunteer).filter(Volunteer.aum_member.is_(True)).count()
    physically_challenged = db.query(Volunteer).filter(Volunteer.physically_challenged.is_(True)).count()
    assigned_to_polling_unit = db.query(Volunteer).filter(Volunteer.polling_unit_id.is_not(None)).count()
    polling_unit_target = db.query(func.coalesce(func.sum(PollingUnit.target_members), 0)).scalar()

    return {
        "total_volunteers": total,
        "male": male,
        "female": female,
        "employed": employed,
        "unemployed": unemployed,
        "aum_members": aum_members,
        "physically_challenged": physically_challenged,
        "assigned_to_polling_unit": assigned_to_polling_unit,
        "unassigned_to_polling_unit": total - assigned_to_polling_unit,
        "polling_unit_target": polling_unit_target,
        "polling_units": db.query(PollingUnit).count(),
    }


@router.get("/volunteers")
def all_volunteers(
    db: Session = Depends(get_db),
    limit: Optional[int] = None,
    sort: Optional[str] = None,
):
    query = db.query(Volunteer)

    if sort:
        try:
            field, order = sort.split(":", 1)
            if hasattr(Volunteer, field):
                column = getattr(Volunteer, field)
                query = query.order_by(column.desc() if order.lower() == "desc" else column.asc())
        except Exception:
            query = query.order_by(Volunteer.id.desc())
    else:
        query = query.order_by(Volunteer.id.desc())

    if limit:
        query = query.limit(limit)

    volunteers = query.all()
    return {"count": len(volunteers), "data": volunteers}


@router.get("/volunteers/recent")
def recent_volunteers(db: Session = Depends(get_db)):
    return db.query(Volunteer).order_by(Volunteer.id.desc()).limit(5).all()


@router.get("/volunteer/{volunteer_id}")
def volunteer_details(volunteer_id: int, db: Session = Depends(get_db)):
    volunteer = db.query(Volunteer).filter(Volunteer.id == volunteer_id).first()
    if not volunteer:
        raise HTTPException(status_code=404, detail="AUM volunteer not found")
    return volunteer


@router.delete("/volunteer/{volunteer_id}")
def delete_volunteer(volunteer_id: int, db: Session = Depends(get_db)):
    volunteer = db.query(Volunteer).filter(Volunteer.id == volunteer_id).first()
    if not volunteer:
        raise HTTPException(status_code=404, detail="AUM volunteer not found")

    for file_path in (volunteer.passport, volunteer.qr_code, volunteer.id_card):
        absolute = resolve_file_path(file_path)
        try:
            if absolute and absolute.is_file():
                absolute.unlink()
        except OSError:
            pass

    db.delete(volunteer)
    db.commit()
    return {"success": True, "message": "AUM volunteer deleted"}


@router.get("/search")
def search_volunteers(keyword: str, db: Session = Depends(get_db)):
    keyword = keyword.strip()
    if not keyword:
        return []

    return (
        db.query(Volunteer)
        .filter(
            Volunteer.name.ilike(f"%{keyword}%")
            | Volunteer.phone.ilike(f"%{keyword}%")
            | Volunteer.registration_no.ilike(f"%{keyword}%")
        )
        .order_by(Volunteer.id.desc())
        .all()
    )


@router.get("/membership-card/{registration_no}")
def download_membership_card(registration_no: str, db: Session = Depends(get_db)):
    volunteer = db.query(Volunteer).filter(Volunteer.registration_no == registration_no).first()
    if not volunteer:
        raise HTTPException(status_code=404, detail="AUM volunteer not found")

    card_path = resolve_file_path(volunteer.id_card)
    if not card_path or not card_path.is_file():
        qr_path = resolve_file_path(volunteer.qr_code)
        generated = Path(generate_membership_card(volunteer, str(qr_path) if qr_path else None))
        volunteer.id_card = os.path.relpath(generated, BASE_DIR)
        db.commit()
        card_path = generated

    return FileResponse(
        path=str(card_path),
        media_type="application/pdf",
        filename=f"{registration_no}-volunteer-card.pdf",
    )


@router.get("/me")
def current_admin(current_user: dict = Depends(get_current_admin)):
    return {
        "username": current_user.get("sub"),
        "role": current_user.get("role"),
        "organization": APP_NAME,
        "short_name": APP_SHORT_NAME,
    }


@router.put("/change-password")
def change_password(password: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_admin)):
    if not password or len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    user = db.query(User).filter(User.username == current_user.get("sub")).first()
    if not user:
        raise HTTPException(status_code=404, detail="Admin account not found")

    user.hashed_password = get_password_hash(password)
    db.commit()
    return {"success": True, "message": "Admin password updated successfully"}


@router.get("/export/excel")
def export_excel(db: Session = Depends(get_db)):
    volunteers = db.query(Volunteer).order_by(Volunteer.id.desc()).all()
    file_path = Path(generate_volunteers_excel(volunteers))
    if not file_path.is_file():
        raise HTTPException(status_code=500, detail="Excel file could not be generated")
    return FileResponse(
        path=str(file_path),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=file_path.name,
    )


@router.get("/export/pdf")
def export_pdf(db: Session = Depends(get_db)):
    volunteers = db.query(Volunteer).order_by(Volunteer.id.desc()).all()
    file_path = Path(generate_volunteer_report(volunteers))
    if not file_path.is_file():
        raise HTTPException(status_code=500, detail="PDF report could not be generated")
    return FileResponse(path=str(file_path), media_type="application/pdf", filename=file_path.name)


def polling_unit_summary(polling_unit, count):
    return {
        "id": polling_unit.id,
        "code": polling_unit.code,
        "name": polling_unit.name,
        "sequence_no": polling_unit.sequence_no,
        "target_members": polling_unit.target_members,
        "registered_members": count,
        "remaining_members": max(polling_unit.target_members - count, 0),
        "ward": {
            "id": polling_unit.ward.id,
            "name": polling_unit.ward.name,
            "lga": polling_unit.ward.lga,
            "state": polling_unit.ward.state,
        },
    }


@router.get("/polling-units")
def polling_units(
    lga: Optional[str] = None,
    ward_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Administrative unit list with each unit's separate member count."""
    query = (
        db.query(PollingUnit, func.count(Volunteer.id).label("member_count"))
        .join(Ward)
        .outerjoin(Volunteer, Volunteer.polling_unit_id == PollingUnit.id)
    )
    if lga:
        query = query.filter(Ward.lga.ilike(lga.strip()))
    if ward_id:
        query = query.filter(PollingUnit.ward_id == ward_id)
    rows = (
        query.group_by(PollingUnit.id)
        .order_by(Ward.lga, Ward.name, PollingUnit.sequence_no, PollingUnit.code)
        .all()
    )
    return {"count": len(rows), "data": [polling_unit_summary(unit, count) for unit, count in rows]}


@router.get("/polling-units/{polling_unit_id}/members")
def polling_unit_members(polling_unit_id: int, db: Session = Depends(get_db)):
    polling_unit = db.query(PollingUnit).filter(PollingUnit.id == polling_unit_id).first()
    if not polling_unit:
        raise HTTPException(status_code=404, detail="Polling unit not found")
    members = (
        db.query(Volunteer)
        .filter(Volunteer.polling_unit_id == polling_unit_id)
        .order_by(Volunteer.id.desc())
        .all()
    )
    return {
        "polling_unit": polling_unit_summary(polling_unit, len(members)),
        "members": members,
    }


@router.put("/polling-units/{polling_unit_id}/target")
def update_polling_unit_target(
    polling_unit_id: int,
    target_members: int,
    db: Session = Depends(get_db),
):
    if target_members < 0:
        raise HTTPException(status_code=422, detail="Target members cannot be negative")
    polling_unit = db.query(PollingUnit).filter(PollingUnit.id == polling_unit_id).first()
    if not polling_unit:
        raise HTTPException(status_code=404, detail="Polling unit not found")
    polling_unit.target_members = target_members
    db.commit()
    db.refresh(polling_unit)
    count = db.query(Volunteer).filter(Volunteer.polling_unit_id == polling_unit.id).count()
    return polling_unit_summary(polling_unit, count)


@router.get("/analytics/lga")
def lga_analytics(db: Session = Depends(get_db)):
    results = (
        db.query(Volunteer.lga, func.count(Volunteer.id))
        .group_by(Volunteer.lga)
        .all()
    )
    return [{"lga": lga, "count": count} for lga, count in results]


@router.get("/analytics/gender")
def gender_analytics(db: Session = Depends(get_db)):
    return {
        "male": db.query(Volunteer).filter(Volunteer.gender.ilike("male")).count(),
        "female": db.query(Volunteer).filter(Volunteer.gender.ilike("female")).count(),
    }


@router.get("/notifications")
def notifications(db: Session = Depends(get_db)):
    recent = db.query(Volunteer).order_by(Volunteer.id.desc()).limit(10).all()
    return [
        {
            "id": volunteer.id,
            "message": f"New AUM volunteer registered: {volunteer.name}",
            "created_at": volunteer.created_at,
            "read": False,
        }
        for volunteer in recent
    ]
