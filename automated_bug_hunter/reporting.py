class ReportGenerator:
    """
    Generates a professional vulnerability report.
    """
    def __init__(self, target, vulnerability):
        self.target = target
        self.vulnerability = vulnerability

    def generate(self):
        """Generates a formatted report string."""
        report = f"""
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
        return report
