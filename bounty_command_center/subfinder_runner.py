import json
from .async_runner import AsyncToolRunner
from .models import Target, Evidence
from typing import List
from .monitoring_config import monitoring_config

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

        if result.aborted:
            self.log.warning(f"Subfinder scan for {target.url} was aborted due to excessive resource usage.")

            details = (
                f"Scan aborted due to sustained resource usage.\\n"
                f"Reason: {result.abort_reason}\\n"
                f"Time to abort: {result.time_to_abort:.2f}s\\n"
                f"Samples collected: {result.samples_collected}\\n"
                f"Peak CPU: {result.peak_cpu:.2%}\\n"
                f"Average CPU: {result.avg_cpu:.2%}\\n"
                f"Peak Memory: {result.peak_mem:.2%}\\n"
                f"Average Memory: {result.avg_mem:.2%}\\n"
                f"Config - Breach Window: {monitoring_config.breach_window_seconds}s\\n"
                f"Config - Poll Interval: {monitoring_config.poll_interval_seconds}s"
            )

            summary = (
                f"Scan aborted due to sustained resource usage "
                f"(CPU > {monitoring_config.cpu_limit:.0%} or "
                f"Mem > {monitoring_config.mem_limit:.0%}) for "
                f"{monitoring_config.breach_window_seconds}s."
            )

            return [Evidence(
                finding_summary=summary,
                reproduction_steps=details,
                severity="Informational",
                target_id=target.id,
            )]
        elif result.return_code == 0 and result.stdout:
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
