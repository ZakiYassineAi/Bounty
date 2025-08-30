from datetime import datetime
from sqlmodel import Session, select
from .database import engine
from .models import Evidence, Target

class EvidenceManager:
    """Manages the lifecycle of evidence using a database."""

    def create_evidence_record(self, target: Target, findings: list[str]):
        """
        Creates new evidence records for a target based on a list of findings.
        """
        if not findings:
            return

        print(f"  -> Logging {len(findings)} new piece(s) of evidence for {target.name}.")

        with Session(engine) as session:
            for finding in findings:
                new_evidence = Evidence(
                    finding_summary=finding,
                    target_id=target.id
                )
                session.add(new_evidence)
            session.commit()

    def update_evidence_status(self, record_id: int, new_status: str) -> bool:
        """
        Updates the status of a specific evidence record by its integer ID.
        """
        with Session(engine) as session:
            evidence_record = session.get(Evidence, record_id)

            if evidence_record:
                evidence_record.status = new_status
                session.add(evidence_record)
                session.commit()
                print(f"Successfully updated status for record {record_id} to '{new_status}'.")
                return True
            else:
                print(f"Error: Record with ID '{record_id}' not found.")
                return False

    def list_evidence(self, status_filter: str | None = None, limit: int = 10):
        """
        Displays collected evidence, with optional filtering by status.
        """
        print(f"\n--- Collected Evidence Log (Filter: {status_filter or 'None'}) ---")

        with Session(engine) as session:
            query = select(Evidence).order_by(Evidence.timestamp.desc())

            if status_filter:
                query = query.where(Evidence.status == status_filter)

            evidence_list = session.exec(query.limit(limit)).all()

            if not evidence_list:
                if status_filter:
                    print(f"No evidence found with status '{status_filter}'.")
                else:
                    print("No evidence has been collected yet.")
                return

            for record in evidence_list:
                # The target is eagerly loaded because of the relationship,
                # but it's good practice to handle the case where it might be None.
                target_name = record.target.name if record.target else "N/A"
                print(f"ID: {record.id}")
                print(f"  Timestamp: {record.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"  Target: {target_name}")
                print(f"  Finding: {record.finding_summary}")
                print(f"  Status: {record.status}")
                print("-" * 25)

            # To show the "more records" count, we need a separate count query
            count_query = select(Evidence)
            if status_filter:
                count_query = count_query.where(Evidence.status == status_filter)
            total_records = len(session.exec(count_query).all())

            if total_records > limit:
                print(f"... and {total_records - limit} more records.")
