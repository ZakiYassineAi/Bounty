from .target_manager import TargetManager
from .tool_integrator import ToolIntegrator
from .evidence_manager import EvidenceManager
from .database import create_db_and_tables

def print_main_menu():
    """Prints the main menu options."""
    print("\n--- Bug Bounty Command Center ---")
    print("1. Manage Targets")
    print("2. Run Scans on a Target")
    print("3. Manage Evidence")
    print("4. Migrate from JSON (Run once)")
    print("5. Exit")
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
    print("\n-- Run Scans --")
    # Check if there are any targets in the DB
    if not tm.get_all_targets():
        print("No targets in the database. Please add a target first.")
        return

    tm.list_targets()
    target_name = input("Enter the name of the target to scan: ")
    target = tm.get_target_by_name(target_name)

    if not target:
        print("Error: Target not found.")
        return

    # ToolIntegrator expects a dictionary-like object, and SQLModel objects work perfectly
    integrator = ToolIntegrator(target)
    findings = integrator.run_all_scans()

    if findings:
        em.create_evidence_record(target, findings)
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
                print("Error: Invalid ID. Please enter a number.")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
        elif choice == '3':
            break
        else:
            print("Invalid choice, please try again.")

def main():
    """Main entry point and CLI loop for the application."""
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
            # Lazy import migrate function to avoid circular dependencies if it grows
            try:
                from .migrate import migrate_data
                migrate_data()
            except ImportError:
                print("Error: Could not find the migration script.")
        elif choice == '5':
            print("Exiting Command Center. Goodbye!")
            break
        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    main()
