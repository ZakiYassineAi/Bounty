from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from .. import schemas
from ..auth import role_checker
from ..models import User
from ..dependencies import get_target_manager
from ..target_manager import TargetManager

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
    tm: TargetManager = Depends(get_target_manager),
    current_user: User = Depends(admin_researcher_access),
):
    """
    Create a new target.
    - **Allowed for:** admin, researcher
    """
    db_target = tm.add_target(name=target.name, url=target.url, scope=target.scope)
    if not db_target:
        raise HTTPException(status_code=400, detail="Target with this name already exists.")
    return db_target

@router.get("/", response_model=List[schemas.TargetRead])
def read_targets(
    skip: int = 0,
    limit: int = Query(default=10, le=100),
    tm: TargetManager = Depends(get_target_manager),
    current_user: User = Depends(any_user_access),
):
    """
    Retrieve all targets with pagination.
    - **Allowed for:** admin, researcher, viewer
    """
    targets = tm.get_all_targets(skip=skip, limit=limit)
    return targets

@router.get("/{target_id}", response_model=schemas.TargetRead)
def read_target(
    target_id: int,
    tm: TargetManager = Depends(get_target_manager),
    current_user: User = Depends(any_user_access),
):
    """
    Retrieve a single target by its ID.
    - **Allowed for:** admin, researcher, viewer
    """
    target = tm.get_target_by_id(target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    return target

@router.put("/{target_id}", response_model=schemas.TargetRead)
def update_target(
    target_id: int,
    target_update: schemas.TargetUpdate,
    tm: TargetManager = Depends(get_target_manager),
    current_user: User = Depends(admin_researcher_access),
):
    """
    Update a target's information.
    - **Allowed for:** admin, researcher
    """
    updated_target = tm.update_target(target_id, target_update.dict(exclude_unset=True))
    if not updated_target:
        raise HTTPException(status_code=404, detail="Target not found")
    return updated_target

@router.delete("/{target_id}", status_code=204)
def delete_target(
    target_id: int,
    tm: TargetManager = Depends(get_target_manager),
    current_user: User = Depends(admin_access),
):
    """
    Delete a target.
    - **Allowed for:** admin
    """
    if not tm.remove_target_by_id(target_id):
        raise HTTPException(status_code=404, detail="Target not found")
    return
