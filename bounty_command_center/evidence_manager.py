from typing import List, Optional, Dict, Any
from sqlmodel import Session, select
from .models import Evidence, Target


class EvidenceManager:
    """Manages CRUD operations for evidence in the database."""

    def create_evidence(
        self,
        db: Session,
        finding_summary: str,
        reproduction_steps: str,
        severity: str,
        status: str,
        target_id: int,
    ) -> Optional[Evidence]:
        """Creates a new evidence record and links it to a target."""
        target = db.get(Target, target_id)
        if not target:
            return None

        new_evidence = Evidence(
            finding_summary=finding_summary,
            reproduction_steps=reproduction_steps,
            severity=severity,
            status=status,
            target_id=target_id,
        )
        db.add(new_evidence)
        db.commit()
        db.refresh(new_evidence)
        return new_evidence

    def get_evidence_by_id(self, db: Session, evidence_id: int) -> Optional[Evidence]:
        """Retrieves a single piece of evidence by its ID."""
        return db.get(Evidence, evidence_id)

    def get_all_evidence(
        self,
        db: Session,
        status_filter: Optional[str] = None,
        target_id_filter: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Evidence]:
        """Retrieves a list of evidence with pagination and optional filters."""
        statement = select(Evidence)
        if status_filter:
            statement = statement.where(Evidence.status == status_filter)
        if target_id_filter:
            statement = statement.where(Evidence.target_id == target_id_filter)

        statement = statement.offset(skip).limit(limit)
        return db.exec(statement).all()

    def update_evidence(
        self, db: Session, evidence_id: int, update_data: Dict[str, Any]
    ) -> Optional[Evidence]:
        """Updates a piece of evidence."""
        evidence = db.get(Evidence, evidence_id)
        if not evidence:
            return None

        for key, value in update_data.items():
            setattr(evidence, key, value)

        db.add(evidence)
        db.commit()
        db.refresh(evidence)
        return evidence

    def delete_evidence_by_id(self, db: Session, evidence_id: int) -> bool:
        """Deletes a piece of evidence by its ID."""
        evidence = db.get(Evidence, evidence_id)
        if evidence:
            db.delete(evidence)
            db.commit()
            return True
        return False

    # --- Existing methods from CLI ---

    def create_evidence_record(self, db: Session, target: Target, findings: List[str]):
        """Creates multiple evidence records from a list of finding strings."""
        for finding in findings:
            evidence = Evidence(finding_summary=finding, target_id=target.id)
            db.add(evidence)
        db.commit()

    def get_evidence(
        self, db: Session, status_filter: Optional[str] = None
    ) -> List[Evidence]:
        """Retrieves a list of evidence, optionally filtered by status."""
        statement = select(Evidence)
        if status_filter:
            statement = statement.where(Evidence.status == status_filter)
        results = db.exec(statement)
        return results.all()

    def update_evidence_status(
        self, db: Session, evidence_id: int, new_status: str
    ) -> bool:
        """Updates the status of a specific piece of evidence."""
        evidence = db.get(Evidence, evidence_id)
        if evidence:
            evidence.status = new_status
            db.add(evidence)
            db.commit()
            return True
        return False
