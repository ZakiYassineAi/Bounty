import json
from .async_runner import AsyncToolRunner
from .models import Target, Evidence
from typing import List

class SqlmapRunner(AsyncToolRunner):
    """
    A tool runner for executing the sqlmap tool.
    """
    async def run(self, target: Target) -> List[Evidence]:
        """
        Runs sqlmap against the target and returns a list of evidence.
        """
        # Command to run sqlmap on the target's URL, in batch mode, with JSON output
        command = ["sqlmap", "-u", target.url, "--batch", "--json"]

        # Execute the command
        result = await self._run_single_command(command, timeout=900) # 15-minute timeout

        if result.return_code == 0 and result.stdout:
            # Parse the output and create evidence
            return self._parse_output(result.stdout, target)
        elif result.stderr:
            self.log.error(f"Sqlmap scan failed for {target.url}: {result.stderr}")

        return []

    def _parse_output(self, stdout: str, target: Target) -> List[Evidence]:
        """
        Parses the JSON output from sqlmap and creates Evidence objects.
        """
        evidence_list = []
        try:
            # sqlmap might produce multiple JSON objects in a stream
            for line in stdout.strip().split('\n'):
                try:
                    log_entry = json.loads(line)
                    if log_entry.get('type') == 'vulnerability':
                        data = log_entry.get('data', {})
                        summary = f"SQL Injection: {data.get('title', 'Untitled')}"
                        severity = self._map_severity(data.get('type'))
                        evidence = Evidence(
                            finding_summary=summary,
                            severity=severity,
                            target_id=target.id
                        )
                        evidence_list.append(evidence)
                except json.JSONDecodeError:
                    self.log.warning(f"Could not decode a line of sqlmap JSON output: {line}")

        except Exception as e:
            self.log.error(f"Failed to parse sqlmap output: {stdout}. Error: {e}")

        return evidence_list

    def _map_severity(self, vuln_type: str) -> str:
        """
        Maps sqlmap vulnerability type to a severity level.
        """
        if 'blind' in vuln_type.lower():
            return "Critical"
        elif 'error' in vuln_type.lower():
            return "High"
        elif 'union' in vuln_type.lower():
            return "High"
        else:
            return "Medium"
