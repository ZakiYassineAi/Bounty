from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from sqlmodel import Session, select

from .. import schemas, models
from ..auth import role_checker
from ..database import get_session

router = APIRouter(
    prefix="/programs",
    tags=["Programs"],
    responses={404: {"description": "Not found"}},
)

# Allow any authenticated user to view program data
any_user_access = role_checker(["admin", "researcher", "viewer"])

@router.get("/", response_model=List[schemas.ProgramReadBasic])
def read_programs(
    skip: int = 0,
    limit: int = Query(default=100, le=200),
    platform_name: str = Query(default=None, description="Filter by platform name (e.g., HackerOne)"),
    db: Session = Depends(get_session),
    current_user: models.User = Depends(any_user_access),
):
    """
    Retrieve all harvested programs with pagination and filtering.
    """
    query = select(models.Program).order_by(models.Program.id)

    if platform_name:
        # This requires a join with the Platform table
        query = query.join(models.Platform).where(models.Platform.name == platform_name)

    query = query.offset(skip).limit(limit)

    programs = db.exec(query).all()
    return programs

@router.get("/{program_id}", response_model=schemas.ProgramRead)
def read_program(
    program_id: int,
    db: Session = Depends(get_session),
    current_user: models.User = Depends(any_user_access),
):
    """
    Retrieve a single program by its ID.
    """
    program = db.get(models.Program, program_id)
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    return program
