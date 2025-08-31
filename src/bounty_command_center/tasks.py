import asyncio
from .celery_app import celery_app
from .database import get_session
from .models import Target
from .tool_integrator import ToolIntegrator
from .logging_setup import get_logger
from sqlmodel import select


log = get_logger(__name__)


@celery_app.task(name="bounty_command_center.tasks.scan_target")
def scan_target(target_id: int):
    """
    Celery task to run a security scan on a target.
    """
    log.info("Starting scan for target_id=%d", target_id)
    with next(get_session()) as session:
        target = session.get(Target, target_id)
        if not target:
            log.error("Target with id %d not found.", target_id)
            return

        tool_integrator = ToolIntegrator(target)
        findings = asyncio.run(tool_integrator.run_all_scans())

        if not findings:
            log.info("No findings for target %s", target.name)
            return

        for evidence in findings:
            session.add(evidence)

        session.commit()
        log.info("Saved %d new findings for target %s", len(findings), target.name)


@celery_app.task(name="bounty_command_center.tasks.scan_new_targets")
def scan_new_targets():
    """
    Periodically scans targets that have no associated evidence.
    """
    log.info("Checking for new targets to scan...")
    with next(get_session()) as session:
        statement = select(Target).where(~Target.evidence.any())
        new_targets = session.exec(statement).all()

        if not new_targets:
            log.info("No new targets found.")
            return

        for target in new_targets:
            log.info("Queueing scan for new target: %s", target.name)
            scan_target.delay(target.id)

        log.info("Queued scans for %d new targets.", len(new_targets))


@celery_app.task(name="bounty_command_center.tasks.rescan_all_targets")
def rescan_all_targets():
    """
    Periodically re-scans all targets.
    """
    log.info("Starting daily rescan of all targets...")
    with next(get_session()) as session:
        targets = session.exec(select(Target)).all()

        if not targets:
            log.info("No targets found to rescan.")
            return

        for target in targets:
            log.info("Queueing daily rescan for target: %s", target.name)
            scan_target.delay(target.id)

        log.info("Queued daily rescans for %d targets.", len(targets))
