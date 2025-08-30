import json
import os
from datetime import datetime
from sqlmodel import Session, select
from .database import engine, create_db_and_tables
from .models import Target, Evidence


def migrate_data():
    """
    Reads data from legacy JSON files and migrates it to the SQLite database.
    - Checks for existing data to prevent duplicates on re-runs.
    - Associates evidence with the correct targets.
    """
    print("Starting data migration...")

    # 1. Create database and tables
    create_db_and_tables()
    print("Database and tables verified.")

    # 2. Load data from JSON files
    try:
        with open("targets.json", "r") as f:
            targets_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        targets_data = []
        print(
            "Warning: 'targets.json' not found or is invalid. Skipping target migration."
        )

    try:
        with open("evidence.json", "r") as f:
            evidence_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        evidence_data = []
        print(
            "Warning: 'evidence.json' not found or is invalid. Skipping evidence migration."
        )

    if not targets_data and not evidence_data:
        print("No data to migrate. Exiting.")
        return

    # 3. Use a session to interact with the database
    with Session(engine) as session:
        # 4. Migrate Targets
        migrated_targets = 0
        target_map = {}  # To map old names to new Target objects

        # First, get all existing target names from the DB
        existing_targets = session.exec(select(Target)).all()
        existing_target_names = {t.name for t in existing_targets}
        target_map = {t.name: t for t in existing_targets}

        for item in targets_data:
            if item["name"] not in existing_target_names:
                new_target = Target(
                    name=item["name"], url=item["url"], scope=item["scope"]
                )
                session.add(new_target)
                target_map[new_target.name] = new_target
                migrated_targets += 1

        session.commit()  # Commit new targets
        print(f"Migrated {migrated_targets} new targets.")

        # Refresh objects to ensure they are bound to the session
        for target in target_map.values():
            session.refresh(target)

        # 5. Migrate Evidence
        migrated_evidence = 0
        for item in evidence_data:
            target_name = item.get("target_name")
            target = target_map.get(target_name)

            if target:
                # A simple check to avoid duplicate evidence for a target
                existing_evidence = session.exec(
                    select(Evidence).where(
                        Evidence.target_id == target.id,
                        Evidence.finding_summary == item["finding_summary"],
                    )
                ).first()

                if not existing_evidence:
                    # FIX: Convert ISO timestamp string to datetime object
                    timestamp_str = item["timestamp"].replace("Z", "+00:00")
                    timestamp_obj = datetime.fromisoformat(timestamp_str)

                    new_evidence = Evidence(
                        timestamp=timestamp_obj,
                        finding_summary=item["finding_summary"],
                        status=item["status"],
                        target_id=target.id,  # Link to the target
                    )
                    session.add(new_evidence)
                    migrated_evidence += 1
            else:
                print(
                    f"Warning: Could not find target '{target_name}' for an evidence record. Skipping."
                )

        session.commit()
        print(f"Migrated {migrated_evidence} new evidence records.")

    print("Migration complete.")


if __name__ == "__main__":
    # This allows the script to be run directly from the command line
    # Make sure to run it from the root directory of the project
    if os.path.basename(os.getcwd()) == "bounty_command_center":
        os.chdir("..")  # Go up to the project root
    migrate_data()
