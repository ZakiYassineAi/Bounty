import markdown
from weasyprint import HTML
from markupsafe import escape
from pathlib import Path
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload


from .config import settings
from .models import Evidence, Target
from .logging_setup import get_logger

log = get_logger(__name__)


def generate_pdf_report_for_target(db: Session, target_id: int) -> bytes | None:
    """
    Generates a PDF report for a given target, including all its evidence.

    Args:
        db: The database session.
        target_id: The ID of the target to report on.

    Returns:
        The PDF report as bytes, or None if generation failed.
    """
    log.info("Generating PDF report for target", target_id=target_id)

    # Use selectinload to eagerly load all related evidence
    query = select(Target).options(selectinload(Target.evidence)).where(Target.id == target_id)
    target = db.exec(query).first()

    if not target:
        log.error("Could not find target to generate report", target_id=target_id)
        return None

    # Start building Markdown content
    markdown_content = f"# Security Report for {target.name}\n\n"
    markdown_content += f"**URL:** {target.url}\n\n"
    markdown_content += f"**Scope:** `{', '.join(target.scope)}`\n\n"
    markdown_content += "---\n\n"

    if not target.evidence:
        markdown_content += "## No findings reported for this target.\n"
    else:
        markdown_content += "## Summary of Findings\n\n"
        for i, evidence in enumerate(target.evidence, 1):
            markdown_content += f"### {i}. {evidence.finding_summary} ({evidence.severity})\n"
            markdown_content += f"- **Status:** {evidence.status.upper()}\n"
            markdown_content += f"- **Timestamp:** {evidence.timestamp.isoformat()}\n\n"
            markdown_content += "**Reproduction Steps:**\n"
            markdown_content += "```\n"
            markdown_content += f"{evidence.reproduction_steps}\n"
            markdown_content += "```\n\n"
            markdown_content += "---\n\n"

    # Convert Markdown to HTML, then to PDF
    try:
        html_content = markdown.markdown(markdown_content)
        pdf_bytes = HTML(string=html_content).write_pdf()
        log.info("Successfully generated PDF report", target_id=target_id, pdf_size=len(pdf_bytes))
        return pdf_bytes
    except Exception as e:
        log.exception("Failed to generate PDF report", target_id=target_id, error=str(e))
        return None


def generate_pdf_report_for_evidence(db: Session, evidence_id: int) -> bytes | None:
    """
    Generates a PDF report for a single piece of evidence.

    Args:
        db: The database session.
        evidence_id: The ID of the evidence to report on.

    Returns:
        The PDF report as bytes, or None if generation failed.
    """
    log.info("Generating PDF report for evidence", evidence_id=evidence_id)

    query = select(Evidence).options(selectinload(Evidence.target)).where(Evidence.id == evidence_id)
    evidence = db.exec(query).first()

    if not evidence:
        log.error("Could not find evidence to generate report", evidence_id=evidence_id)
        return None

    # Sanitize user-provided data from the evidence object
    safe_summary = escape(evidence.finding_summary)
    safe_steps = escape(evidence.reproduction_steps)
    safe_severity = escape(evidence.severity)

    # Load the Markdown template from file
    try:
        template_path = Path(__file__).parent / "templates" / "evidence_report.md"
        with open(template_path, "r", encoding="utf-8") as f:
            markdown_template = f.read()
    except FileNotFoundError:
        log.exception("Evidence report template not found.", path=str(template_path))
        return None

    # Populate the template
    markdown_content = markdown_template.format(
        summary=safe_summary,
        steps=safe_steps,
        severity=safe_severity,
    )

    # Convert Markdown to HTML, then to PDF
    try:
        html_content = markdown.markdown(markdown_content)
        pdf_bytes = HTML(string=html_content).write_pdf()
        log.info("Successfully generated PDF report for evidence", evidence_id=evidence_id, pdf_size=len(pdf_bytes))
        return pdf_bytes
    except Exception as e:
        log.exception("Failed to generate PDF report for evidence", evidence_id=evidence_id, error=str(e))
        return None


def generate_markdown_report(db: Session, evidence_id: int) -> Path | None:
    """
    Generates a Markdown report for a given piece of evidence.

    Args:
        db: The database session.
        evidence_id: The ID of the evidence to report.

    Returns:
        The path to the generated report file, or None if generation failed.
    """
    log.info("Attempting to generate report for evidence", evidence_id=evidence_id)

    # Query for the evidence and eagerly load the related target
    query = select(Evidence).where(Evidence.id == evidence_id)
    evidence = db.exec(query).first()

    if not evidence:
        log.error("Could not find evidence to generate report", evidence_id=evidence_id)
        return None

    # Ensure the target is loaded
    if not evidence.target:
        log.error("Evidence record is not linked to a target", evidence_id=evidence_id)
        return None

    # 1. Prepare file path and directory
    export_dir = Path(settings.reporting.export_directory)
    export_dir.mkdir(parents=True, exist_ok=True)

    timestamp_str = evidence.timestamp.strftime('%Y%m%d-%H%M%S')

    filename = settings.reporting.filename_template.format(
        target_name=evidence.target.name.replace(" ", "_"),
        evidence_id=evidence.id,
        timestamp=timestamp_str
    )
    report_path = export_dir / filename

    # 2. Build Markdown content
    content = f"""
# Bug Bounty Report: {evidence.finding_summary}

**Target:** {evidence.target.name}
**URL:** {evidence.target.url}
**Scope:** `{', '.join(evidence.target.scope)}`

---

## Finding Details

- **Evidence ID:** {evidence.id}
- **Timestamp:** {evidence.timestamp.isoformat()}
- **Status:** {evidence.status.upper()}
- **Severity:** {evidence.severity}
- **Finding Summary:** {evidence.finding_summary}

---

## Description

{evidence.reproduction_steps}

## Proof of Concept

(Add your proof of concept here, including code snippets, screenshots, or HTTP requests.)

"""

    # 3. Write content to file
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(content)
        log.info("Successfully generated report", path=str(report_path))
        return report_path
    except IOError as e:
        log.exception("Failed to write report to file", path=str(report_path), error=str(e))
        return None
