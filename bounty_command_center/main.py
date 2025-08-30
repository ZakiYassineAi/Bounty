import asyncio
from .target_manager import TargetManager
from .tool_integrator import ToolIntegrator
from .evidence_manager import EvidenceManager
from .database import create_db_and_tables
from .async_runner import AsyncToolRunner
from .logging_setup import setup_logging, get_logger

# It's good practice to get a logger at the module level
log = get_logger(__name__)

def print_main_menu():
    """Prints the main menu options."""
    print("\n--- Bug Bounty Command Center ---")
    print("1. Manage Targets")
    print("2. Run Scans on a Target")
    print("3. Manage Evidence")
    print("4. Migrate from JSON (Run once)")
    print("5. Run Async Demo")
    print("6. Exit")
    print("---------------------------------")

def manage_targets_menu(tm: TargetManager):
    """Handles the target management sub-menu."""
    while True:
        print("\n-- Target Management --")
        print("1. List All Targets")
        print("2. Add New Target")
        print("3. Remove a Target")
        print("4. Back to Main Menu")
        choice = input("Enter your choice: ")

        if choice == '1':
            tm.list_targets()
        elif choice == '2':
            name = input("Enter target name: ")
            url = input("Enter target URL: ")
            scope_input = input("Enter scope (comma-separated): ")
            scope = [s.strip() for s in scope_input.split(',')]
            tm.add_target(name, url, scope)
        elif choice == '3':
            name = input("Enter name of target to remove: ")
            tm.remove_target(name)
        elif choice == '4':
            break
        else:
            print("Invalid choice, please try again.")

def run_scans_menu(tm: TargetManager, em: EvidenceManager):
    """Handles the scanning sub-menu."""
    log.info("Starting scan menu...")
    # Check if there are any targets in the DB
    if not tm.get_all_targets():
        log.warning("No targets in database to scan.")
        print("No targets in the database. Please add a target first.")
        return

    tm.list_targets()
    target_name = input("Enter the name of the target to scan: ")
    target = tm.get_target_by_name(target_name)

    if not target:
        log.error("Target not found for scanning", target_name=target_name)
        print("Error: Target not found.")
        return

    integrator = ToolIntegrator(target)
    findings = integrator.run_all_scans()

    if findings:
        em.create_evidence_record(target, findings)
    log.info("Scan complete.")
    print("Scan complete.")

def manage_evidence_menu(em: EvidenceManager):
    """Handles the evidence management and triage sub-menu."""
    while True:
        print("\n-- Evidence Management --")
        print("1. List Evidence (All or by Status)")
        print("2. Update Evidence Status")
        print("3. Back to Main Menu")
        choice = input("Enter your choice: ")

        if choice == '1':
            filter_status = input("Enter status to filter by (e.g., new, reviewed) or leave blank for all: ")
            em.list_evidence(status_filter=filter_status if filter_status else None)
        elif choice == '2':
            try:
                record_id_str = input("Enter the ID of the evidence record to update: ")
                record_id = int(record_id_str)
                new_status = input("Enter the new status (e.g., reviewed, false_positive, confirmed): ")
                em.update_evidence_status(record_id, new_status)
            except ValueError:
                log.warning("Invalid evidence ID entered", input=record_id_str)
                print("Error: Invalid ID. Please enter a number.")
            except Exception as e:
                log.exception("Error updating evidence status")
                print(f"An unexpected error occurred: {e}")
        elif choice == '3':
            break
        else:
            print("Invalid choice, please try again.")

async def run_async_demo():
    """Runs a demonstration of the AsyncToolRunner."""
    log.info("Starting async tool runner demo.")
    print("\n--- Async Runner Demo ---")

    runner = AsyncToolRunner()

    # A list of commands to run in parallel
    commands_to_run = [
        ["ping", "-c", "1", "8.8.8.8"],  # A quick network command
        ["sleep", "1"],                  # A short wait
        ["ls", "-la", "/tmp"],           # A quick filesystem command
        ["sleep", "5"],                  # A command that will time out
        ["not-a-real-command"],          # A command that will fail
    ]

    # Run the commands with a 2-second timeout
    results = await runner.run_commands(commands_to_run, timeout=2)

    print("\n--- Demo Results ---")
    for res in results:
        print(f"COMMAND: {res.command}")
        print(f"  Timed Out: {res.timed_out}")
        print(f"  Return Code: {res.return_code}")
        if res.stdout:
            print(f"  STDOUT:\n{res.stdout}")
        if res.stderr:
            print(f"  STDERR:\n{res.stderr}")
        print("-" * 20)
    log.info("Async demo finished.")

def main():
    """Main entry point and CLI loop for the application."""
    # Setup logging as the first thing
    setup_logging()

    log.info("Application starting up...")
    # Ensure the database and tables are created on startup
    create_db_and_tables()

    tm = TargetManager()
    em = EvidenceManager()

    while True:
        print_main_menu()
        choice = input("Enter your choice: ")

        if choice == '1':
            manage_targets_menu(tm)
        elif choice == '2':
            run_scans_menu(tm, em)
        elif choice == '3':
            manage_evidence_menu(em)
        elif choice == '4':
            try:
                from .migrate import migrate_data
                log.info("User initiated data migration.")
                migrate_data()
            except ImportError:
                log.error("Migration script not found.")
                print("Error: Could not find the migration script.")
        elif choice == '5':
            # Run the async function using asyncio.run()
            asyncio.run(run_async_demo())
        elif choice == '6':
            log.info("Application shutting down.")
            print("Exiting Command Center. Goodbye!")
            break
        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    main()
