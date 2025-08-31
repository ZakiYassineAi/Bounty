from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from sqlmodel import Session
from .. import schemas, evidence_manager
from ..auth import role_checker
from ..models import User
from ..database import get_session

router = APIRouter(
    prefix="/evidence",
    tags=["Evidence"],
    responses={404: {"description": "Not found"}},
)

# Role-based access control dependencies
admin_researcher_access = role_checker(["admin", "researcher"])
admin_access = role_checker(["admin"])
any_user_access = role_checker(["admin", "researcher", "viewer"])

@router.post("/", response_model=schemas.EvidenceRead, status_code=201)
def create_evidence(
    evidence: schemas.EvidenceCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(admin_researcher_access),
):
    """
    Create a new piece of evidence.
    - **Allowed for:** admin, researcher
    """
    em = evidence_manager.EvidenceManager()
    db_evidence = em.create_evidence(
        db=db,
        finding_summary=evidence.finding_summary,
        reproduction_steps=evidence.reproduction_steps,
        severity=evidence.severity,
        status=evidence.status,
        target_id=evidence.target_id,
    )
    if not db_evidence:
        raise HTTPException(status_code=400, detail="Could not create evidence. The target ID may be invalid.")
    return db_evidence

@router.get("/", response_model=List[schemas.EvidenceRead])
def read_evidence(
    status: Optional[str] = None,
    target_id: Optional[int] = None,
    skip: int = 0,
    limit: int = Query(default=10, le=100),
    db: Session = Depends(get_session),
    current_user: User = Depends(any_user_access),
):
    """
    Retrieve all evidence with pagination and filtering.
    - **Allowed for:** admin, researcher, viewer
    """
    em = evidence_manager.EvidenceManager()
    evidence_list = em.get_all_evidence(
        db=db,
        status_filter=status,
        target_id_filter=target_id,
        skip=skip,
        limit=limit,
    )
    return evidence_list

@router.get("/{evidence_id}", response_model=schemas.EvidenceRead)
def read_single_evidence(
    evidence_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(any_user_access),
):
    """
    Retrieve a single piece of evidence by its ID.
    - **Allowed for:** admin, researcher, viewer
    """
    em = evidence_manager.EvidenceManager()
    evidence = em.get_evidence_by_id(db=db, evidence_id=evidence_id)
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return evidence

@router.put("/{evidence_id}", response_model=schemas.EvidenceRead)
def update_evidence(
    evidence_id: int,
    evidence_update: schemas.EvidenceUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(admin_researcher_access),
):
    """
    Update a piece of evidence.
    - **Allowed for:** admin, researcher
    """
    em = evidence_manager.EvidenceManager()
    updated_evidence = em.update_evidence(db=db, evidence_id=evidence_id, update_data=evidence_update.dict(exclude_unset=True))
    if not updated_evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return updated_evidence

@router.delete("/{evidence_id}", status_code=204)
def delete_evidence(
    evidence_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(admin_access),
):
    """
    Delete a piece of evidence.
    - **Allowed for:** admin
    """
    em = evidence_manager.EvidenceManager()
    if not em.delete_evidence_by_id(db=db, evidence_id=evidence_id):
        raise HTTPException(status_code=404, detail="Evidence not found")
    return
