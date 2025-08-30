from target_manager import TargetManager
from tool_integrator import ToolIntegrator
from evidence_manager import EvidenceManager

def print_main_menu():
    """Prints the main menu options."""
    print("\n--- Bug Bounty Command Center ---")
    print("1. Manage Targets")
    print("2. Run Scans on a Target")
    print("3. Manage Evidence")
    print("4. Exit")
    print("---------------------------------")

def manage_targets_menu(tm):
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

def run_scans_menu(tm, em):
    """Handles the scanning sub-menu."""
    print("\n-- Run Scans --")
    tm.list_targets()
    if not tm.targets:
        return
    target_name = input("Enter the name of the target to scan: ")
    target = tm.get_target_by_name(target_name)

    if not target:
        print("Error: Target not found.")
        return

    integrator = ToolIntegrator(target)
    findings = integrator.run_all_scans()

    if findings:
        em.create_evidence_record(target, findings)
    print("Scan complete.")

def manage_evidence_menu(em):
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
            record_id = input("Enter the ID of the evidence record to update: ")
            new_status = input("Enter the new status (e.g., reviewed, false_positive, confirmed): ")
            em.update_evidence_status(record_id, new_status)
        elif choice == '3':
            break
        else:
            print("Invalid choice, please try again.")

def main():
    """Main entry point and CLI loop for the application."""
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
            print("Exiting Command Center. Goodbye!")
            break
        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    main()
