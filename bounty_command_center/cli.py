import typer
from rich.console import Console
from rich.table import Table
import asyncio
from typing_extensions import Annotated
from urllib.parse import urlparse

from . import target_manager, evidence_manager, report_generator
from .async_runner import AsyncToolRunner
from .logging_setup import setup_logging, get_logger
from .database import create_db_and_tables
from .config import settings

# Create a Typer app instance and sub-apps for organization
app = typer.Typer(help="A command-line tool to manage bug bounty hunting activities.")
target_app = typer.Typer(name="target", help="Manage targets.")
evidence_app = typer.Typer(name="evidence", help="Manage evidence.")
user_app = typer.Typer(name="user", help="Manage users.")
app.add_typer(target_app)
app.add_typer(evidence_app)
app.add_typer(user_app)

# Create a Rich console for beautiful output
console = Console()

# Instantiate managers
from . import user_manager
tm = target_manager.TargetManager()
em = evidence_manager.EvidenceManager()
um = user_manager.UserManager()
runner = AsyncToolRunner()

# --- User Commands ---

@user_app.command("create")
def create_user(
    username: str = typer.Option(..., "--username", "-u", help="The username for the new user."),
    password: str = typer.Option(..., "--password", "-p", prompt=True, hide_input=True, help="The password for the new user."),
    role: str = typer.Option("viewer", "--role", "-r", help="The role for the new user (admin, researcher, viewer)."),
):
    """Creates a new user in the database."""
    log = get_logger("create_user")
    log.info("Attempting to create a new user", username=username, role=role)

    # Validate role
    if role not in ["admin", "researcher", "viewer"]:
        console.print(f"[red]✖[/red] Invalid role '{role}'. Must be one of: admin, researcher, viewer.")
        raise typer.Exit(code=1)

    user = um.create_user(username, password, role)
    if user:
        console.print(f"[green]✔[/green] Successfully created user: {username} with role {role}")
    else:
        console.print(f"[red]✖[/red] Failed to create user. Username may already exist.")
        raise typer.Exit(code=1)

@app.callback()
def main_callback():
    """Initialize database and logging before running any command."""
    setup_logging()
    create_db_and_tables()

# --- Target Commands ---

@target_app.command("add")
def add_target(
    name: str = typer.Option(..., "--name", "-n", help="The unique name of the target."),
    url: str = typer.Option(..., "--url", "-u", help="The primary URL for the target."),
    scope: str = typer.Option(..., "--scope", "-s", help="A comma-separated list of items in scope."),
):
    """Adds a new target to the database."""
    log = get_logger("add_target")
    log.info("Attempting to add new target", name=name, url=url)
    scope_list = [s.strip() for s in scope.split(',')]
    if tm.add_target(name, url, scope_list):
        console.print(f"[green]✔[/green] Successfully added target: {name}")
    else:
        console.print(f"[red]✖[/red] Failed to add target. It may already exist.")
        raise typer.Exit(code=1)

@target_app.command("list")
def list_targets():
    """Lists all targets in the database."""
    targets = tm.get_all_targets()
    if not targets:
        console.print("[yellow]No targets found in the database.[/yellow]")
        return
    table = Table(title="Bug Bounty Targets")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="magenta")
    table.add_column("URL", style="green")
    table.add_column("Scope")
    for target in targets:
        table.add_row(str(target.id), target.name, target.url, ", ".join(target.scope))
    console.print(table)

@target_app.command("remove")
def remove_target(
    name: str = typer.Argument(..., help="The name of the target to remove."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Bypass confirmation prompt.")
):
    """Removes a target from the database."""
    log = get_logger("remove_target")
    log.info("Attempting to remove target", name=name)
    if yes or typer.confirm(f"Are you sure you want to delete the target '{name}'?"):
        if tm.remove_target(name):
            console.print(f"[green]✔[/green] Successfully removed target: {name}")
        else:
            console.print(f"[red]✖[/red] Failed to remove target. It may not exist.")
            raise typer.Exit(code=1)
    else:
        console.print("Operation cancelled.")

# --- Evidence Commands ---

@evidence_app.command("list")
def list_evidence(status: Annotated[str, typer.Option("--status", "-s", help="Filter by evidence status.")] = None):
    """Lists collected evidence, optionally filtering by status."""
    console.print(f"\n--- Collected Evidence Log (Filter: {status or 'All'}) ---")
    evidence_list = em.get_evidence(status_filter=status)
    if not evidence_list:
        console.print("[yellow]No evidence found matching the criteria.[/yellow]")
        return
    table = Table(title="Collected Evidence")
    table.add_column("ID", style="cyan")
    table.add_column("Target", style="magenta")
    table.add_column("Status", style="yellow")
    table.add_column("Finding")
    table.add_column("Timestamp")
    for ev in evidence_list:
        table.add_row(
            str(ev.id), ev.target.name if ev.target else "N/A", ev.status,
            ev.finding_summary, ev.timestamp.strftime('%Y-%m-%d %H:%M')
        )
    console.print(table)

@evidence_app.command("update")
def update_evidence_status(
    evidence_id: int = typer.Argument(..., help="The ID of the evidence to update."),
    new_status: str = typer.Argument(..., help="The new status (e.g., reviewed, confirmed).")
):
    """Updates the status of a piece of evidence."""
    log = get_logger("update_evidence")
    log.info("Attempting to update evidence status", id=evidence_id, new_status=new_status)
    if em.update_evidence_status(evidence_id, new_status):
        console.print(f"[green]✔[/green] Successfully updated evidence {evidence_id} to '{new_status}'.")
    else:
        console.print(f"[red]✖[/red] Failed to update evidence. The ID may not exist.")
        raise typer.Exit(code=1)

@evidence_app.command("report")
def export_report(evidence_id: int = typer.Argument(..., help="The ID of the evidence to export.")):
    """Exports a specific piece of evidence to a Markdown report."""
    log = get_logger("export_report")
    log.info("Exporting report for evidence", evidence_id=evidence_id)
    report_path = report_generator.generate_markdown_report(evidence_id)
    if report_path:
        console.print(f"[green]✔[/green] Successfully generated report at: {report_path}")
    else:
        console.print(f"[red]✖[/red] Failed to generate report. Check logs for details.")
        raise typer.Exit(code=1)

# --- Main App Commands ---

async def _run_scan_async(target_name: str):
    """Async helper function to run scans and process results."""
    log = get_logger("run_scan")
    target = tm.get_target_by_name(target_name)
    if not target:
        console.print(f"[red]✖[/red] Target '{target_name}' not found.")
        raise typer.Exit(code=1)

    console.print(f"Running scans on [bold magenta]{target.name}[/bold magenta]...")

    # Define a set of real, non-intrusive commands
    hostname = urlparse(target.url).hostname
    if not hostname:
        console.print(f"[red]✖[/red] Could not parse hostname from URL: {target.url}")
        raise typer.Exit(code=1)

    commands_to_run = [
        ["ping", "-c", "1", hostname],
        ["curl", "-s", "-I", target.url],
        ["curl", "-s", "-L", f"{target.url}/robots.txt"],
    ]

    # Run commands using the async runner, sourcing timeout from config
    timeout = settings.async_runner.default_timeout
    results = await runner.run_commands(commands_to_run, timeout=timeout)

    # Process results and create evidence
    new_findings = []
    for res in results:
        if res.return_code == 0 and res.stdout:
            finding = f"[{res.command}] - Success\n---\n{res.stdout}"
            new_findings.append(finding)
        elif res.return_code != 0:
            finding = f"[{res.command}] - Failed (Code: {res.return_code})\n---\n{res.stderr}"
            new_findings.append(finding)

    if new_findings:
        em.create_evidence_record(target, new_findings)
        console.print(f"[green]✔[/green] Scan complete. Found {len(new_findings)} new findings.")
    else:
        console.print("[green]✔[/green] Scan complete. No new findings.")

@app.command()
def run_scan(target_name: str = typer.Argument(..., help="The name of the target to scan.")):
    """Runs a set of reconnaissance scans on a specific target."""
    asyncio.run(_run_scan_async(target_name))

@app.command()
def migrate():
    """Runs the data migration utility to import data from old JSON files."""
    log = get_logger("migrate")
    console.print("Starting data migration from JSON files...")
    try:
        from .migrate import migrate_data
        migrate_data()
        console.print("[green]✔[/green] Data migration completed.")
    except ImportError:
        log.error("Migration script not found.")
        console.print("[red]✖[/red] Could not find the migration script.")
        raise typer.Exit(code=1)
    except Exception as e:
        log.exception("An error occurred during migration.")
        console.print(f"[red]✖[/red] An error occurred during migration: {e}")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
