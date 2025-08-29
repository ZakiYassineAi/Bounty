import os
import re

class ReportGenerator:
    """
    Generates a professional vulnerability report and saves it to a file.
    """
    def __init__(self, target, vulnerability):
        self.target = target
        self.vulnerability = vulnerability
        self.report_dir = 'reports'

    def _generate_report_content(self):
        """Generates the formatted report string."""
        return f"""
===================================================
 VULNERABILITY REPORT
===================================================
TARGET: {self.target['name']}
URL: {self.target['url']}
---------------------------------------------------
VULNERABILITY: {self.vulnerability['type']}
SEVERITY: {self.vulnerability['severity']}
ESTIMATED PAYOUT: ${self.vulnerability['payout']}
---------------------------------------------------
DESCRIPTION:
A potential {self.vulnerability['type']} vulnerability was identified during an automated scan.

STEPS TO REPRODUCE (PoC):
1. [Automated] Sent a series of test payloads to endpoints on {self.target['url']}.
2. [Automated] Monitored responses for anomalies indicating a flaw.
3. [Verification Needed] Atypical response received, suggesting a {self.vulnerability['severity']} vulnerability.

IMPACT:
The potential impact of this vulnerability could include unauthorized data access, session hijacking, or full system compromise, depending on the context.

RECOMMENDED MITIGATION:
It is recommended that a security engineer manually verify this finding. If confirmed, apply appropriate sanitization and validation to all user-supplied input, and review access control policies.
===================================================
"""

    def save_to_file(self):
        """Saves the generated report to a unique file."""
        # Ensure the reports directory exists
        if not os.path.exists(self.report_dir):
            os.makedirs(self.report_dir)

        # Sanitize vulnerability type for the filename
        sanitized_vuln_type = re.sub(r'[^a-zA-Z0-9]', '', self.vulnerability['type'])

        # Create a unique filename
        filename = f"{self.target['name']}_{sanitized_vuln_type}_{self.vulnerability['severity']}.txt"
        filepath = os.path.join(self.report_dir, filename)

        # Generate the report content
        report_content = self._generate_report_content()

        # Write the report to the file
        with open(filepath, 'w') as f:
            f.write(report_content)

        print(f"  -> Report saved to: {filepath}")
