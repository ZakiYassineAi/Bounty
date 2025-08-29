import random

class VulnerabilityScanner:
    """
    A comprehensive vulnerability scanner that uses various tools.
    """
    def __init__(self, target):
        self.target = target
        self.tools = {
            'xss_scanner': XSSPayloadTester(),
            'sql_injector': SQLInjectionTester(),
            'csrf_tester': CSRFTester(),
            'info_disclosure': InfoLeakScanner(),
            'auth_bypass': AuthenticationTester()
        }

    def comprehensive_scan(self):
        """Runs a comprehensive scan using all available tools."""
        print(f"\\nStarting comprehensive scan for {self.target['name']}...")
        results = []
        for tool_name, tool in self.tools.items():
            vulnerability = tool.scan(self.target)
            if vulnerability:
                results.append(vulnerability)
        return results

# --- Mock Tool Subclasses ---

class XSSPayloadTester:
    def scan(self, target):
        """Simulates scanning for XSS vulnerabilities."""
        if random.random() < 0.1: # 10% chance to find a mock XSS flaw
            return {"type": "Cross-Site Scripting (XSS)", "severity": "Medium", "payout": random.randint(100, 500)}
        return None

class SQLInjectionTester:
    def scan(self, target):
        """Simulates scanning for SQL Injection vulnerabilities."""
        if random.random() < 0.05: # 5% chance
            return {"type": "SQL Injection", "severity": "High", "payout": random.randint(2000, 10000)}
        return None

class CSRFTester:
    def scan(self, target):
        """Simulates scanning for CSRF vulnerabilities."""
        if random.random() < 0.08: # 8% chance
            return {"type": "Cross-Site Request Forgery (CSRF)", "severity": "Medium", "payout": random.randint(500, 2000)}
        return None

class InfoLeakScanner:
    def scan(self, target):
        """Simulates scanning for Information Disclosure."""
        if random.random() < 0.15: # 15% chance
            return {"type": "Information Disclosure", "severity": "Low", "payout": random.randint(100, 500)}
        return None

class AuthenticationTester:
    def scan(self, target):
        """Simulates scanning for Authentication Bypasses."""
        if random.random() < 0.06: # 6% chance
            return {"type": "Authentication Bypass", "severity": "Critical", "payout": random.randint(5000, 20000)}
        return None
