import json
import os
import uuid
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
        """
        if not findings:
            return

        timestamp = datetime.now().isoformat()
        print(f"  -> Logging {len(findings)} new piece(s) of evidence for {target['name']}.")

        for finding in findings:
            new_record = {
                'id': str(uuid.uuid4()), # Add a unique ID for each record
                'timestamp': timestamp,
                'target_name': target['name'],
                'target_url': target['url'],
                'finding_summary': finding,
                'status': 'new' # Default status
            }
            self.evidence_log.append(new_record)

        self._save_evidence()

    def update_evidence_status(self, record_id, new_status):
        """
        Updates the status of a specific evidence record.
        :param record_id: The unique ID of the record to update.
        :param new_status: The new status (e.g., 'reviewed', 'false_positive').
        """
        record_found = False
        for record in self.evidence_log:
            if record.get('id') == record_id:
                record['status'] = new_status
                record_found = True
                break

        if record_found:
            self._save_evidence()
            print(f"Successfully updated status for record {record_id} to '{new_status}'.")
            return True
        else:
            print(f"Error: Record with ID '{record_id}' not found.")
            return False

    def list_evidence(self, status_filter=None, limit=10):
        """
        Displays collected evidence, with optional filtering by status.
        :param status_filter: (Optional) A string to filter evidence by status.
        :param limit: The maximum number of records to display.
        """
        print(f"\n--- Collected Evidence Log (Filter: {status_filter or 'None'}) ---")

        if not self.evidence_log:
            print("No evidence has been collected yet.")
            return

        # Sort evidence by timestamp, most recent first
        sorted_evidence = sorted(self.evidence_log, key=lambda x: x['timestamp'], reverse=True)

        # Filter by status if a filter is provided
        if status_filter:
            display_list = [r for r in sorted_evidence if r['status'] == status_filter]
        else:
            display_list = sorted_evidence

        if not display_list:
            print(f"No evidence found with status '{status_filter}'.")
            return

        for i, record in enumerate(display_list[:limit]):
            print(f"ID: {record.get('id')}")
            print(f"  Timestamp: {record['timestamp']}")
            print(f"  Target: {record['target_name']}")
            print(f"  Finding: {record['finding_summary']}")
            print(f"  Status: {record['status']}")
            print("-" * 25)

        if len(display_list) > limit:
            print(f"... and {len(display_list) - limit} more records.")

        return display_list # Return the list for the CLI to use
