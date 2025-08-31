from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List

from sqlmodel import Session
from .. import schemas, target_manager
from ..auth import role_checker
from ..models import User
from ..database import get_session
from ..tasks import scan_target

router = APIRouter(
    prefix="/targets",
    tags=["Targets"],
    responses={404: {"description": "Not found"}},
)

# Role-based access control dependencies
admin_researcher_access = role_checker(["admin", "researcher"])
admin_access = role_checker(["admin"])
any_user_access = role_checker(["admin", "researcher", "viewer"])

@router.post("/", response_model=schemas.TargetRead, status_code=201)
def create_target(
    target: schemas.TargetCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(admin_researcher_access),
):
    """
    Create a new target.
    - **Allowed for:** admin, researcher
    """
    tm = target_manager.TargetManager()
    db_target = tm.add_target(db=db, name=target.name, url=target.url, scope=target.scope)
    if not db_target:
        raise HTTPException(status_code=400, detail="Target with this name already exists.")

    # Asynchronously trigger a scan of the new target
    scan_target.delay(db_target.id)

    return db_target

@router.get("/", response_model=List[schemas.TargetRead])
def read_targets(
    skip: int = 0,
    limit: int = Query(default=10, le=100),
    db: Session = Depends(get_session),
    current_user: User = Depends(any_user_access),
):
    """
    Retrieve all targets with pagination.
    - **Allowed for:** admin, researcher, viewer
    """
    tm = target_manager.TargetManager()
    targets = tm.get_all_targets(db=db, skip=skip, limit=limit)
    return targets

@router.get("/{target_id}", response_model=schemas.TargetRead)
def read_target(
    target_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(any_user_access),
):
    """
    Retrieve a single target by its ID.
    - **Allowed for:** admin, researcher, viewer
    """
    tm = target_manager.TargetManager()
    target = tm.get_target_by_id(db=db, target_id=target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    return target

@router.put("/{target_id}", response_model=schemas.TargetRead)
def update_target(
    target_id: int,
    target_update: schemas.TargetUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(admin_researcher_access),
):
    """
    Update a target's information.
    - **Allowed for:** admin, researcher
    """
    tm = target_manager.TargetManager()
    updated_target = tm.update_target(db=db, target_id=target_id, update_data=target_update.dict(exclude_unset=True))
    if not updated_target:
        raise HTTPException(status_code=404, detail="Target not found")
    return updated_target

@router.delete("/{target_id}", status_code=204)
def delete_target(
    target_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(admin_access),
):
    """
    Delete a target.
    - **Allowed for:** admin
    """
    tm = target_manager.TargetManager()
    if not tm.remove_target_by_id(db=db, target_id=target_id):
        raise HTTPException(status_code=404, detail="Target not found")
    return
