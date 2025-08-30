import json
from .async_runner import AsyncToolRunner
from .models import Target, Evidence
from typing import List

class DalfoxRunner(AsyncToolRunner):
    """
    A tool runner for executing the dalfox tool.
    """
    async def run(self, target: Target) -> List[Evidence]:
        """
        Runs dalfox against the target and returns a list of evidence.
        """
        # Command to run dalfox on the target's URL and output in JSON format
        command = ["dalfox", "url", target.url, "--format", "json"]

        # Execute the command
        result = await self._run_single_command(command, timeout=600) # 10-minute timeout

        if result.aborted:
            self.log.warning(f"Dalfox scan for {target.url} was aborted due to excessive resource usage.")
            return [Evidence(
                finding_summary="Scan aborted due to excessive resource usage.",
                severity="Informational",
                target_id=target.id,
            )]
        elif result.return_code == 0 and result.stdout:
            # Parse the output and create evidence
            return self._parse_output(result.stdout, target)
        elif result.stderr:
            self.log.error(f"Dalfox scan failed for {target.url}: {result.stderr}")

        return []

    def _parse_output(self, stdout: str, target: Target) -> List[Evidence]:
        """
        Parses the JSON output from dalfox and creates Evidence objects.
        """
        evidence_list = []
        try:
            data = json.loads(stdout)
            for poc in data.get('pocs', []):
                summary = poc.get('message_str', 'XSS vulnerability found')
                severity = poc.get('severity', 'Medium')
                reproduction = f"PoC URL: {poc.get('data', 'N/A')}"

                evidence = Evidence(
                    finding_summary=summary,
                    severity=severity,
                    reproduction_steps=reproduction,
                    target_id=target.id
                )
                evidence_list.append(evidence)
        except json.JSONDecodeError as e:
            self.log.error(f"Failed to parse dalfox JSON output: {stdout}. Error: {e}")

        return evidence_list
