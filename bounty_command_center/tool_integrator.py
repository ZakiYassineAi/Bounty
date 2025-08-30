import requests
import random

# These classes simulate finding specific types of vulnerabilities.
class XSSSimulator:
    def scan(self, target):
        """Simulates scanning for XSS vulnerabilities."""
        if random.random() < 0.1: # 10% chance
            return "[simulated-xss][medium] Reflected XSS found on search.php?query="
        return None

class SQLiSimulator:
    def scan(self, target):
        """Simulates scanning for SQL Injection vulnerabilities."""
        if random.random() < 0.05: # 5% chance
            return "[simulated-sqli][high] SQL Injection vulnerability in 'id' parameter."
        return None

class CSRFSimulator:
    def scan(self, target):
        """Simulates scanning for CSRF vulnerabilities."""
        if random.random() < 0.08: # 8% chance
            return "[simulated-csrf][medium] CSRF token not validated on account_update.php"
        return None

class GitLeakChecker:
    """Checks for an exposed .git/config file."""
    def scan(self, target):
        url = target.get('url', '')
        if not url:
            return None

        # Ensure the URL has a scheme
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'http://' + url

        git_config_url = f"{url.rstrip('/')}/.git/config"

        try:
            # Set a timeout to avoid hanging indefinitely
            response = requests.get(git_config_url, timeout=5)
            # Check if the file is found and seems to be a git config
            if response.status_code == 200 and '[core]' in response.text:
                return f"[git-leak][high] Exposed .git/config file found at {git_config_url}"
        except requests.exceptions.RequestException as e:
            # This will catch connection errors, timeouts, etc.
            # In a real scenario, you might want to log this error differently.
            print(f"  ->  [GitLeakChecker] An error occurred while scanning {git_config_url}: {e}")
            return None

        return None

class AuthBypassSimulator:
    def scan(self, target):
        """Simulates scanning for Authentication Bypasses."""
        if random.random() < 0.06: # 6% chance
            return "[simulated-authbypass][critical] Authentication bypass by manipulating session cookie."
        return None


class ToolIntegrator:
    """
    Integrates and runs various simulated scanning tools.
    This version uses a probabilistic model to simulate finding vulnerabilities.
    """
    def __init__(self, target):
        """
        Initializes the ToolIntegrator with a specific target.
        :param target: A dictionary representing the target.
        """
        if not isinstance(target, dict) or 'name' not in target:
            raise ValueError("Invalid target provided to ToolIntegrator")
        self.target = target
        self.simulators = {
            'XSS': XSSSimulator(),
            'SQLi': SQLiSimulator(),
            'CSRF': CSRFSimulator(),
            'GitLeak': GitLeakChecker(),
            'AuthBypass': AuthBypassSimulator()
        }

    def run_all_scans(self):
        """
        Runs all configured tool simulations and returns any findings.
        """
        print(f"\n--- Running All Scans on {self.target['name']} ---")
        all_findings = []

        for name, simulator in self.simulators.items():
            print(f"  -> Running {name} scan...")
            finding = simulator.scan(self.target)
            if finding:
                all_findings.append(finding)

        if not all_findings:
            print("  -> No findings from any tool in this scan.")

        return all_findings
