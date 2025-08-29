import random

class BountyTargetScanner:
    """
    Scans for and prioritizes bug bounty programs.
    In a real scenario, this would scrape websites. Here, it uses a mock list.
    """
    def __init__(self):
        self.mock_programs = []

    def scan_for_programs(self):
        """Simulates scanning for programs by creating a mock list."""
        print("Scanning for bug bounty programs...")
        self.mock_programs = [
            {'name': 'StartupX', 'url': 'https://startupx.com', 'max_bounty': 1500, 'program_age_months': 6, 'vuln_count': 5, 'response_time_score': 8},
            {'name': 'Legacy Corp', 'url': 'https://legacy-corp.com', 'max_bounty': 5000, 'program_age_months': 60, 'vuln_count': 150, 'response_time_score': 4},
            {'name': 'Fintech Innovators', 'url': 'https://fintech-innovate.io', 'max_bounty': 10000, 'program_age_months': 12, 'vuln_count': 25, 'response_time_score': 9},
            {'name': 'GamerZ United', 'url': 'https://gamerz-united.net', 'max_bounty': 2500, 'program_age_months': 24, 'vuln_count': 40, 'response_time_score': 6},
            {'name': 'HealthApp', 'url': 'https://healthapp.dev', 'max_bounty': 500, 'program_age_months': 3, 'vuln_count': 2, 'response_time_score': 7},
            {'name': 'CryptoEx', 'url': 'https://crypto-ex.com', 'max_bounty': 50000, 'program_age_months': 18, 'vuln_count': 80, 'response_time_score': 5},
        ]
        print(f"Found {len(self.mock_programs)} programs.")
        return self.mock_programs

def prioritize_targets(targets):
    """
    Scores and sorts targets based on multiple factors, as per the user's formula.
    Lower program_age_months is better, so we will invert it for scoring.
    """
    print("\\nPrioritizing targets based on scoring model...")
    scored_targets = []
    for target in targets:
        # The user's plan implies newer is better for program_age.
        # So we create an 'age_score' that is higher for lower ages.
        # A simple inversion: max_age (e.g., 60 months) - actual_age
        age_score = max(0, 60 - target['program_age_months'])

        score = (
            target['max_bounty'] * 0.4 +
            age_score * 0.2 +
            target['vuln_count'] * 0.3 +
            target['response_time_score'] * 0.1
        )
        scored_targets.append((target, score))

    # Sort targets by score in descending order
    sorted_targets = sorted(scored_targets, key=lambda x: x[1], reverse=True)

    print("Prioritization complete.")
    # Return just the list of target dictionaries, ordered by score
    return [target for target, score in sorted_targets]
