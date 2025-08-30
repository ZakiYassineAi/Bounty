from pathlib import Path
from sqlmodel import Session, select

from .config import settings
from .database import engine
from .models import Evidence
from .logging_setup import get_logger

log = get_logger(__name__)

def generate_markdown_report(evidence_id: int) -> Path | None:
    """
    Generates a Markdown report for a given piece of evidence.

    Args:
        evidence_id: The ID of the evidence to report.

    Returns:
        The path to the generated report file, or None if generation failed.
    """
    log.info("Attempting to generate report for evidence", evidence_id=evidence_id)

    with Session(engine) as session:
        # Query for the evidence and eagerly load the related target
        query = select(Evidence).where(Evidence.id == evidence_id)
        evidence = session.exec(query).first()

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
- **Finding Summary:** {evidence.finding_summary}

---

## Description

(Please provide a detailed description of the vulnerability, including steps to reproduce, impact, and suggested remediation.)

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
