import json
from .async_runner import AsyncToolRunner
from .models import Target, Evidence
from typing import List

class SubfinderRunner(AsyncToolRunner):
    """
    A tool runner for executing the subfinder tool.
    """
    async def run(self, target: Target) -> List[Evidence]:
        """
        Runs subfinder against the target and returns a list of evidence.
        """
        # Command to run subfinder on the target's URL and output in JSON format
        command = ["subfinder", "-d", target.url, "-json"]

        # Execute the command
        result = await self._run_single_command(command, timeout=300) # 5-minute timeout

        if result.return_code == 0 and result.stdout:
            # Parse the output and create evidence
            return self._parse_output(result.stdout, target)
        elif result.stderr:
            self.log.error(f"Subfinder scan failed for {target.url}: {result.stderr}")

        return []

    def _parse_output(self, stdout: str, target: Target) -> List[Evidence]:
        """
        Parses the JSON output from subfinder and creates Evidence objects.
        """
        evidence_list = []
        for line in stdout.strip().split('\n'):
            try:
                finding = json.loads(line)
                subdomain = finding.get("host")
                if subdomain:
                    summary = f"Subdomain discovered: {subdomain}"
                    evidence = Evidence(
                        finding_summary=summary,
                        severity="Informational",
                        target_id=target.id
                    )
                    evidence_list.append(evidence)
            except json.JSONDecodeError as e:
                self.log.error(f"Failed to parse subfinder JSON output line: {line}. Error: {e}")
            except Exception as e:
                self.log.error(f"An unexpected error occurred while parsing subfinder output: {line}. Error: {e}")

        return evidence_list
