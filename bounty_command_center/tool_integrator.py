import asyncio
from .models import Target, Evidence
from .subfinder_runner import SubfinderRunner
from .dalfox_runner import DalfoxRunner
from .sqlmap_runner import SqlmapRunner
from .nuclei_runner import NucleiRunner
from typing import List

class ToolIntegrator:
    """
    Integrates and runs various scanning tools.
    """
    def __init__(self, target: Target):
        """
        Initializes the ToolIntegrator with a specific target.
        :param target: A Target model object.
        """
        if not isinstance(target, Target):
            raise ValueError("Invalid target provided to ToolIntegrator, expected a Target object.")
        self.target = target
        self.runners = {
            'Subfinder': SubfinderRunner(),
            'Dalfox': DalfoxRunner(),
            'Sqlmap': SqlmapRunner(),
            'Nuclei': NucleiRunner(),
        }

    async def run_all_scans(self) -> List[Evidence]:
        """
        Runs all configured tool runners and returns any findings.
        """
        print(f"\n--- Running All Scans on {self.target.name} ---")
        all_findings = []

        tasks = []
        for name, runner in self.runners.items():
            print(f"  -> Queuing {name} scan...")
            tasks.append(runner.run(self.target))

        results = await asyncio.gather(*tasks)
        for result in results:
            all_findings.extend(result)

        if not all_findings:
            print("  -> No findings from any tool in this scan.")

        return all_findings
