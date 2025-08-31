import asyncio
import random
import uuid
from .celery_app import celery_app
from .database import get_session
from .models import Target
from .tool_integrator import ToolIntegrator
from .logging_setup import get_logger
from sqlmodel import select
from .harvester_aggregator import HarvesterAggregator
from .normalization_service import NormalizationService
from .report_generator import generate_run_report

log = get_logger(__name__)

@celery_app.task(name="bounty_command_center.tasks.scan_target")
def scan_target(target_id: int):
    """
    Celery task to run a security scan on a target.
    """
    log.info("Starting scan for target_id=%d", target_id)
    # Using get_session directly because this task is about DB interaction
    with get_session() as session:
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
    with get_session() as session:
        statement = select(Target).where(~Target.evidence.any())
        new_targets = session.exec(statement).all()

        if not new_targets:
            log.info("No new targets found.")
            return

        for target in new_targets:
            log.info("Queueing scan for new target: %s", target.name)
            scan_target.delay(target.id)

        log.info("Queued scans for %d new targets.", len(new_targets))

import time

@celery_app.task(name="bounty_command_center.tasks.harvest_platform")
def harvest_platform(platform: str):
    """
    Runs the harvester for a single specified platform, normalizes the data,
    and generates a summary report.
    """
    run_id = str(uuid.uuid4())
    log.info("Running full harvest and report for platform: %s", platform, extra={"run_id": run_id})
    start_time = time.time()
    stats = {}
    error_info = None

    try:
        harvester_aggregator = HarvesterAggregator()
        normalization_service = NormalizationService()

        with get_session() as db:
            harvester_aggregator.run(db, platform, run_id=run_id)
            stats = normalization_service.run(db, platform)
    except Exception as e:
        log.exception("An unexpected error occurred during harvest task", platform=platform, run_id=run_id)
        error_info = str(e)
    finally:
        end_time = time.time()
        duration = end_time - start_time
        stats['duration'] = f"{duration:.2f} seconds"
        stats['error'] = error_info
        generate_run_report(platform, stats, run_id)

@celery_app.task(name="bounty_command_center.tasks.schedule_all_platform_harvests")
def schedule_all_platform_harvests():
    """
    Schedules harvesting tasks for all platforms with a random jitter.
    This task is meant to be run on a schedule by Celery Beat.
    """
    log.info("Scheduling harvest for all platforms with jitter...")
    platforms = ["intigriti", "yeswehack", "openbugbounty", "synack"]
    max_jitter_seconds = 600

    for platform in platforms:
        jitter = random.uniform(0, max_jitter_seconds)
        log.info("Scheduling harvest for %s with a %.2f second delay.", platform, jitter)
        harvest_platform.apply_async(args=[platform], countdown=jitter)

@celery_app.task(name="bounty_command_center.tasks.rescan_all_targets")
def rescan_all_targets():
    """
    Periodically re-scans all targets.
    """
    log.info("Starting daily rescan of all targets...")
    with get_session() as session:
        targets = session.exec(select(Target)).all()

        if not targets:
            log.info("No targets found to rescan.")
            return

        for target in targets:
            log.info("Queueing daily rescan for target: %s", target.name)
            scan_target.delay(target.id)

        log.info("Queued daily rescans for %d targets.", len(targets))
