from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session
import io

from .. import report_generator
from ..auth import role_checker
from ..models import User
from ..database import get_session

router = APIRouter(
    prefix="/api/reports",
    tags=["Reports"],
    responses={404: {"description": "Not found"}},
)

# Role-based access control
any_user_access = role_checker(["admin", "researcher", "viewer"])


@router.get("/export/{target_id}", response_class=StreamingResponse)
def export_target_report(
    target_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(any_user_access),
):
    """
    Export a PDF report for a specific target.
    - **Allowed for:** admin, researcher, viewer
    """
    pdf_bytes = report_generator.generate_pdf_report_for_target(db, target_id)
    if not pdf_bytes:
        raise HTTPException(
            status_code=404,
            detail="Report could not be generated. Target not found or error in generation.",
        )

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=target_report_{target_id}.pdf"
        },
    )


@router.get("/export/evidence/{evidence_id}", response_class=StreamingResponse)
def export_evidence_report(
    evidence_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(any_user_access),
):
    """
    Export a PDF report for a single piece of evidence.
    - **Allowed for:** admin, researcher, viewer
    """
    pdf_bytes = report_generator.generate_pdf_report_for_evidence(db, evidence_id)
    if not pdf_bytes:
        raise HTTPException(
            status_code=404,
            detail="Report could not be generated. Evidence not found or error in generation.",
        )

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=evidence_report_{evidence_id}.pdf"
        },
    )
