from datetime import datetime
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
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
            # Use session.get for a primary key lookup, it's faster.
            evidence_record = session.get(Evidence, record_id)

            if evidence_record:
                evidence_record.status = new_status
                session.add(evidence_record)
                session.commit()
                return True
            else:
                return False

    def get_evidence(self, status_filter: str | None = None) -> list[Evidence]:
        """
        Retrieves a list of evidence records, with optional filtering by status.
        This method returns data, it does not print to console.
        """
        with Session(engine) as session:
            # Use selectinload to eagerly load the related Target object
            # This prevents DetachedInstanceError when accessing evidence.target later
            query = select(Evidence).options(selectinload(Evidence.target)).order_by(Evidence.timestamp.desc())

            if status_filter:
                query = query.where(Evidence.status == status_filter)

            evidence_list = session.exec(query).all()
            return evidence_list
