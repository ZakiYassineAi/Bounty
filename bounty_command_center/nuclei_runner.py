import asyncio
import json
from typing import List
from .models import Target, Evidence

class NucleiRunner:
    """
    Runs Nuclei scans and parses the output.
    """
    async def run(self, target: Target) -> List[Evidence]:
        """
        Runs a Nuclei scan on the given target.
        :param target: A Target model object.
        :return: A list of Evidence objects found by the scan.
        """
        print(f"  -> Running Nuclei scan on {target.url}")

        # Command to run Nuclei
        # We use -jsonl for line-delimited JSON output
        # We select a basic set of templates for this example
        command = [
            "nuclei",
            "-target", target.url,
            "-jsonl",
            "-tags", "cve,exposed-panels,misconfiguration,default-logins",
            "-severity", "medium,high,critical",
            "-silent",
            "-no-color",
        ]

        # Run the command asynchronously
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            print(f"  -> Nuclei scan on {target.url} failed with exit code {process.returncode}")
            print(f"  -> Stderr: {stderr.decode()}")
            return []

        # Parse the JSONL output
        findings = []
        if stdout:
            for line in stdout.decode().strip().split('\n'):
                if not line:
                    continue
                try:
                    finding_data = json.loads(line)
                    evidence = Evidence(
                        target_id=target.id,
                        finding_summary=finding_data.get("info", {}).get("name", "Unnamed Nuclei Finding"),
                        reproduction_steps=json.dumps(finding_data, indent=2),
                        severity=finding_data.get("info", {}).get("severity", "informational").capitalize(),
                    )
                    findings.append(evidence)
                except json.JSONDecodeError:
                    print(f"  -> Error decoding JSON from Nuclei output: {line}")

        if findings:
            print(f"  -> Found {len(findings)} new findings with Nuclei for {target.url}")

        return findings
