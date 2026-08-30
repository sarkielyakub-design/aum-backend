# AUM Backend

Backend API for **AMB. USMAN MOVEMENT (AUM)**.

> Together for Progress.

## Stack
- FastAPI
- SQLAlchemy
- PostgreSQL
- JWT authentication
- QR verification
- Volunteer card PDF generation
- Excel export
- PDF reporting
- Admin dashboard APIs

## Main API areas
- `/api/auth`
- `/api/volunteers`
- `/api/admin`

## Registration numbers
New volunteers receive IDs in the format:

`AUM-000001`

## Public uploads
- `/uploads/passports/...`
- `/uploads/cards/...`
- `/uploads/qr/...`

## Ward and polling-unit administration

Registration locations are sourced from imported ward/polling-unit records, not
created from member form input.  Each new registration is linked to a ward and a
polling unit; the unit holds its own member target (200 by default) and member
list.

After deploying this version, import the supplied files from the project root:

```bash
python -m app.scripts.import_polling_units /path/to/KIYAWA.xlsx /path/to/DUTSE.xlsx --target 200
python -m app.scripts.backfill_volunteer_locations --dry-run
python -m app.scripts.backfill_volunteer_locations
```

The backfill only assigns an existing volunteer when its saved LGA, ward and
unit exactly match imported data; unmatched records are left unchanged.

Public registration lookups:

- `GET /api/volunteers/locations/wards?lga=DUTSE`
- `GET /api/volunteers/locations/polling-units?ward_id=...`

Administrative views:

- `GET /api/admin/polling-units`
- `GET /api/admin/polling-units/{id}/members`
- `PUT /api/admin/polling-units/{id}/target?target_members=200`

## Environment
Configure:
- `DATABASE_URL`
- `SECRET_KEY`
- `ALGORITHM`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `FRONTEND_ORIGINS`
- `BACKEND_URL`
# aum-backend
