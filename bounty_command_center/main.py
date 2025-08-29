from target_manager import TargetManager
from tool_integrator import ToolIntegrator
from evidence_manager import EvidenceManager

def print_main_menu():
    """Prints the main menu options."""
    print("\n--- Bug Bounty Command Center ---")
    print("1. Manage Targets")
    print("2. Run Scans on a Target")
    print("3. View Evidence Log")
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
            em.list_evidence()
        elif choice == '4':
            print("Exiting Command Center. Goodbye!")
            break
        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    main()
