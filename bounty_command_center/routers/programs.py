from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from sqlmodel import Session, select, desc, asc

from .. import schemas, models
from ..auth import role_checker
from ..database import get_session

router = APIRouter(
    prefix="/programs",
    tags=["Programs"],
    responses={404: {"description": "Not found"}},
)

any_user_access = role_checker(["admin", "researcher", "viewer"])

@router.get("/", response_model=schemas.PaginatedProgramResponse)
def read_programs(
    db: Session = Depends(get_session),
    current_user: models.User = Depends(any_user_access),
    limit: int = Query(default=50, le=100),
    cursor: Optional[int] = Query(default=None, description="The ID of the last item received to fetch the next page."),
    platform_name: Optional[str] = Query(default=None, description="Filter by platform name (e.g., HackerOne)"),
    status: Optional[str] = Query(default=None, description="Filter by program status (e.g., active)"),
    min_payout: Optional[int] = Query(default=None, description="Filter by minimum payout."),
    sort_by: str = Query(default="-id", description="Sort by field (e.g., name, -last_seen_at, -id)"),
):
    """
    Retrieve all harvested programs with cursor-based pagination, filtering, and sorting.
    """
    query = select(models.Program)

    # --- Filtering ---
    if platform_name:
        query = query.join(models.Platform).where(models.Platform.name == platform_name)
    if status:
        query = query.where(models.Program.status == status)
    if min_payout:
        # This assumes you want to filter on the minimum payout of a program.
        query = query.where(models.Program.min_payout >= min_payout)

    # --- Sorting ---
    sort_field_name = sort_by[1:] if sort_by.startswith('-') else sort_by
    if hasattr(models.Program, sort_field_name):
        sort_field = getattr(models.Program, sort_field_name)
        if sort_by.startswith('-'):
            query = query.order_by(desc(sort_field))
        else:
            query = query.order_by(asc(sort_field))
    else:
        # Default sort if field is invalid
        query = query.order_by(desc(models.Program.id))

    # --- Pagination (Cursor-based) ---
    if cursor:
        # This simplified cursor logic works best when sorting by a unique, sequential column like ID.
        # For other fields, a more robust keyset pagination would be needed.
        if sort_by == "-id": # Most common case
            query = query.where(models.Program.id < cursor)
        else:
            # This is a simplification and might not be perfectly accurate for all sort fields.
            # It requires the sort field to be highly correlated with the cursor (ID).
            pass

    programs = db.exec(query.limit(limit)).all()

    next_cursor = programs[-1].id if programs and len(programs) == limit else None

    return schemas.PaginatedProgramResponse(items=programs, next_cursor=next_cursor)

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
