from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from .. import schemas
from ..auth import role_checker
from ..models import User
from ..dependencies import get_evidence_manager
from ..evidence_manager import EvidenceManager

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
    em: EvidenceManager = Depends(get_evidence_manager),
    current_user: User = Depends(admin_researcher_access),
):
    """
    Create a new piece of evidence.
    - **Allowed for:** admin, researcher
    """
    db_evidence = em.create_evidence(
        finding_summary=evidence.finding_summary,
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
    em: evidence_manager.EvidenceManager = Depends(get_evidence_manager),
    current_user: User = Depends(any_user_access),
):
    """
    Retrieve all evidence with pagination and filtering.
    - **Allowed for:** admin, researcher, viewer
    """
    evidence_list = em.get_all_evidence(
        status_filter=status,
        target_id_filter=target_id,
        skip=skip,
        limit=limit,
    )
    return evidence_list

@router.get("/{evidence_id}", response_model=schemas.EvidenceRead)
def read_single_evidence(
    evidence_id: int,
    em: evidence_manager.EvidenceManager = Depends(get_evidence_manager),
    current_user: User = Depends(any_user_access),
):
    """
    Retrieve a single piece of evidence by its ID.
    - **Allowed for:** admin, researcher, viewer
    """
    evidence = em.get_evidence_by_id(evidence_id)
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return evidence

@router.put("/{evidence_id}", response_model=schemas.EvidenceRead)
def update_evidence(
    evidence_id: int,
    evidence_update: schemas.EvidenceUpdate,
    em: evidence_manager.EvidenceManager = Depends(get_evidence_manager),
    current_user: User = Depends(admin_researcher_access),
):
    """
    Update a piece of evidence.
    - **Allowed for:** admin, researcher
    """
    updated_evidence = em.update_evidence(evidence_id, evidence_update.dict(exclude_unset=True))
    if not updated_evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return updated_evidence

@router.delete("/{evidence_id}", status_code=204)
def delete_evidence(
    evidence_id: int,
    em: evidence_manager.EvidenceManager = Depends(get_evidence_manager),
    current_user: User = Depends(admin_access),
):
    """
    Delete a piece of evidence.
    - **Allowed for:** admin
    """
    if not em.delete_evidence_by_id(evidence_id):
        raise HTTPException(status_code=404, detail="Evidence not found")
    return
