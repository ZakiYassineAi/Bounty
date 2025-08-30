from typing import List, Optional, Dict, Any
from sqlmodel import Session, select
from .database import engine
from .models import Evidence, Target

class EvidenceManager:
    """Manages CRUD operations for evidence in the database."""

    def create_evidence(self, finding_summary: str, status: str, target_id: int) -> Optional[Evidence]:
        """
        Creates a new evidence record and links it to a target.

        Args:
            finding_summary: A summary of the finding.
            status: The status of the evidence (e.g., 'new', 'reviewed').
            target_id: The ID of the target this evidence belongs to.

        Returns:
            The created Evidence object, or None if the target_id is invalid.
        """
        with Session(engine) as session:
            # Check if the target exists
            target = session.get(Target, target_id)
            if not target:
                return None

            new_evidence = Evidence(
                finding_summary=finding_summary,
                status=status,
                target_id=target_id
            )
            session.add(new_evidence)
            session.commit()
            session.refresh(new_evidence)
            return new_evidence

    def get_evidence_by_id(self, evidence_id: int) -> Optional[Evidence]:
        """Retrieves a single piece of evidence by its ID."""
        with Session(engine) as session:
            return session.get(Evidence, evidence_id)

    def get_all_evidence(
        self,
        status_filter: Optional[str] = None,
        target_id_filter: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Evidence]:
        """
        Retrieves a list of evidence with pagination and optional filters.
        """
        with Session(engine) as session:
            statement = select(Evidence)
            if status_filter:
                statement = statement.where(Evidence.status == status_filter)
            if target_id_filter:
                statement = statement.where(Evidence.target_id == target_id_filter)

            statement = statement.offset(skip).limit(limit)
            return session.exec(statement).all()

    def update_evidence(self, evidence_id: int, update_data: Dict[str, Any]) -> Optional[Evidence]:
        """Updates a piece of evidence."""
        with Session(engine) as session:
            evidence = session.get(Evidence, evidence_id)
            if not evidence:
                return None

            for key, value in update_data.items():
                setattr(evidence, key, value)

            session.add(evidence)
            session.commit()
            session.refresh(evidence)
            return evidence

    def delete_evidence_by_id(self, evidence_id: int) -> bool:
        """Deletes a piece of evidence by its ID."""
        with Session(engine) as session:
            evidence = session.get(Evidence, evidence_id)
            if evidence:
                session.delete(evidence)
                session.commit()
                return True
            return False

    # --- Existing methods from CLI ---

    def create_evidence_record(self, target: Target, findings: List[str]):
        """Creates multiple evidence records from a list of finding strings."""
        with Session(engine) as session:
            for finding in findings:
                evidence = Evidence(finding_summary=finding, target_id=target.id)
                session.add(evidence)
            session.commit()

    def get_evidence(self, status_filter: Optional[str] = None) -> List[Evidence]:
        """Retrieves a list of evidence, optionally filtered by status."""
        with Session(engine) as session:
            statement = select(Evidence)
            if status_filter:
                statement = statement.where(Evidence.status == status_filter)
            results = session.exec(statement)
            return results.all()

    def update_evidence_status(self, evidence_id: int, new_status: str) -> bool:
        """Updates the status of a specific piece of evidence."""
        with Session(engine) as session:
            evidence = session.get(Evidence, evidence_id)
            if evidence:
                evidence.status = new_status
                session.add(evidence)
                session.commit()
                return True
            return False
