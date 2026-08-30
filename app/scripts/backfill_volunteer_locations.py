"""Link existing volunteers only where their saved text values exactly match imports."""

import argparse
from sqlalchemy import func, or_

from app.db.session import SessionLocal
from app.models.location import PollingUnit, Ward
from app.models.volunteer import Volunteer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    db = SessionLocal()
    assigned = unmatched = 0
    try:
        volunteers = db.query(Volunteer).filter(Volunteer.polling_unit_id.is_(None)).all()
        for volunteer in volunteers:
            unit = (
                db.query(PollingUnit)
                .join(Ward)
                .filter(
                    func.lower(Ward.lga) == (volunteer.lga or "").strip().lower(),
                    func.lower(Ward.name) == (volunteer.ward or "").strip().lower(),
                    or_(
                        func.lower(PollingUnit.name) == (volunteer.unit or "").strip().lower(),
                        func.lower(PollingUnit.code) == (volunteer.unit or "").strip().lower(),
                    ),
                )
                .first()
            )
            if not unit:
                unmatched += 1
                continue
            volunteer.ward_id = unit.ward_id
            volunteer.polling_unit_id = unit.id
            assigned += 1
        if args.dry_run:
            db.rollback()
        else:
            db.commit()
        print(f"{assigned} assigned, {unmatched} left unassigned" + (" (dry run)" if args.dry_run else ""))
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
