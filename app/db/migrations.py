"""Small, idempotent schema upgrades for deployments created before locations.

The project predates a migration framework and already creates tables at startup.
This module safely upgrades the existing PostgreSQL ``volunteers`` table without
changing or guessing any existing member location values.
"""

from sqlalchemy import inspect, text


def upgrade_location_schema(engine) -> None:
    """Add the location foreign-key columns to an existing volunteers table."""
    inspector = inspect(engine)
    if "volunteers" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("volunteers")}
    statements = []
    if "ward_id" not in columns:
        statements.append("ALTER TABLE volunteers ADD COLUMN ward_id INTEGER")
    if "polling_unit_id" not in columns:
        statements.append("ALTER TABLE volunteers ADD COLUMN polling_unit_id INTEGER")

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))

        # PostgreSQL permits CREATE INDEX IF NOT EXISTS, making repeat deploys safe.
        connection.execute(
            text("CREATE INDEX IF NOT EXISTS ix_volunteers_ward_id ON volunteers (ward_id)")
        )
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_volunteers_polling_unit_id "
                "ON volunteers (polling_unit_id)"
            )
        )
        # New databases receive these through metadata.create_all().  Add them
        # to existing databases as well, without validating or rewriting old
        # member data (the new columns begin as NULL).
        connection.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint WHERE conname = 'fk_volunteers_ward_id'
                ) THEN
                    ALTER TABLE volunteers
                    ADD CONSTRAINT fk_volunteers_ward_id
                    FOREIGN KEY (ward_id) REFERENCES wards(id);
                END IF;
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint WHERE conname = 'fk_volunteers_polling_unit_id'
                ) THEN
                    ALTER TABLE volunteers
                    ADD CONSTRAINT fk_volunteers_polling_unit_id
                    FOREIGN KEY (polling_unit_id) REFERENCES polling_units(id);
                END IF;
            END $$;
        """))
