from targets import BountyTargetScanner, prioritize_targets
from scanner import VulnerabilityScanner
from reporting import ReportGenerator
from database import load_db, save_db, add_vulnerability_record, mark_target_as_scanned

def main():
    """
    Main function to run the complete, integrated bug hunting process
    with persistence and file-based reporting.
    """
    print("==============================================")
    print("  Initializing Automated Bug Hunter System (v2)")
    print("==============================================")

    # Load the database
    db = load_db()

    # 1. Scan for targets
    target_scanner = BountyTargetScanner()
    programs = target_scanner.scan_for_programs()

    # 2. Prioritize targets
    prioritized_targets = prioritize_targets(programs)

    print("\\n--- Starting Scans on Prioritized Targets ---")

    # 3. Loop through targets and scan
    total_vulnerabilities_found_this_session = 0
    for target in prioritized_targets:
        # Check if target has already been scanned
        if target['name'] in db['scanned_targets']:
            print(f"\\nSkipping {target['name']}: Already scanned.")
            continue

        scanner = VulnerabilityScanner(target)
        found_vulnerabilities = scanner.comprehensive_scan()

        # 4. Generate reports and update database for findings
        if found_vulnerabilities:
            print(f"  -> Found {len(found_vulnerabilities)} vulnerabilities for {target['name']}!")
            total_vulnerabilities_found_this_session += len(found_vulnerabilities)
            for vuln in found_vulnerabilities:
                # Add to database
                add_vulnerability_record(db, target, vuln)

                # Generate and save the report to a file
                report_generator = ReportGenerator(target, vuln)
                report_generator.save_to_file()
        else:
            print(f"  -> No vulnerabilities found for {target['name']}.")

        # Mark the target as scanned for this session
        mark_target_as_scanned(db, target)

    # 5. Save the updated database
    save_db(db)

    print("==============================================")
    print(f"         Scan Complete")
    print(f"   Vulnerabilities Found (This Session): {total_vulnerabilities_found_this_session}")
    print(f"   Total Vulnerabilities in DB: {len(db['found_vulnerabilities'])}")
    print("==============================================")
    print("System Shutting Down.")


if __name__ == "__main__":
    main()
