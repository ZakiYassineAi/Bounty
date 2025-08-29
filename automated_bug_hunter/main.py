from targets import BountyTargetScanner, prioritize_targets
from scanner import VulnerabilityScanner
from reporting import ReportGenerator

def main():
    """
    Main function to run the complete, integrated bug hunting process.
    """
    print("==============================================")
    print("  Initializing Automated Bug Hunter System")
    print("==============================================")

    # 1. Scan for targets
    target_scanner = BountyTargetScanner()
    programs = target_scanner.scan_for_programs()

    # 2. Prioritize targets
    prioritized_targets = prioritize_targets(programs)

    print("\\n--- Starting Scans on Prioritized Targets ---")

    # 3. Loop through targets and scan
    total_vulnerabilities_found = 0
    for target in prioritized_targets:
        scanner = VulnerabilityScanner(target)
        found_vulnerabilities = scanner.comprehensive_scan()

        # 4. Generate reports for findings
        if found_vulnerabilities:
            print(f"  -> Found {len(found_vulnerabilities)} vulnerabilities for {target['name']}!")
            total_vulnerabilities_found += len(found_vulnerabilities)
            for vuln in found_vulnerabilities:
                report_generator = ReportGenerator(target, vuln)
                report = report_generator.generate()
                print(report)
        else:
            print(f"  -> No vulnerabilities found for {target['name']}.")

    print("==============================================")
    print(f"         Scan Complete")
    print(f"   Total Vulnerabilities Found: {total_vulnerabilities_found}")
    print("==============================================")
    print("System Shutting Down.")


if __name__ == "__main__":
    main()
