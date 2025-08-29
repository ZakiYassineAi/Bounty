import json
import os
from datetime import datetime

class EvidenceManager:
    """Manages the lifecycle of evidence collected from scans."""
    def __init__(self, db_file='evidence.json'):
        self.db_file = db_file
        self.evidence_log = self._load_evidence()

    def _load_evidence(self):
        """Loads evidence from the JSON database, creating it if it doesn't exist."""
        if not os.path.exists(self.db_file):
            return []
        if os.path.getsize(self.db_file) == 0:
            return []
        with open(self.db_file, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []

    def _save_evidence(self):
        """Saves the current evidence log to the JSON database."""
        with open(self.db_file, 'w') as f:
            json.dump(self.evidence_log, f, indent=4)

    def create_evidence_record(self, target, findings):
        """
        Creates a new evidence record for a target based on a list of findings.
        :param target: The target dictionary.
        :param findings: A list of strings, where each string is a finding from a tool.
        """
        if not findings:
            return

        timestamp = datetime.now().isoformat()
        print(f"  -> Logging {len(findings)} new piece(s) of evidence for {target['name']}.")

        for finding in findings:
            new_record = {
                'timestamp': timestamp,
                'target_name': target['name'],
                'target_url': target['url'],
                'finding_summary': finding,
                'status': 'new' # Status can be 'new', 'reviewed', 'reported', etc.
            }
            self.evidence_log.append(new_record)

        self._save_evidence()

    def list_evidence(self, limit=10):
        """
        Displays all collected evidence in a formatted way, showing the most recent first.
        :param limit: The maximum number of records to display.
        """
        print("\n--- Collected Evidence Log ---")
        if not self.evidence_log:
            print("No evidence has been collected yet.")
            return

        # Sort evidence by timestamp, most recent first
        sorted_evidence = sorted(self.evidence_log, key=lambda x: x['timestamp'], reverse=True)

        for i, record in enumerate(sorted_evidence[:limit]):
            print(f"Record {i+1}:")
            print(f"  Timestamp: {record['timestamp']}")
            print(f"  Target: {record['target_name']}")
            print(f"  Finding: {record['finding_summary']}")
            print(f"  Status: {record['status']}")
            print("-" * 25)

        if len(sorted_evidence) > limit:
            print(f"... and {len(sorted_evidence) - limit} more records.")
