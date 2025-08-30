import pytest
import httpx
from bounty_command_center.harvester.bugcrowd_harvester import BugcrowdHarvester

@pytest.mark.vcr
async def test_bugcrowd_harvester_fetch():
    """
    Tests the BugcrowdHarvester's fetch_programs method using a VCR cassette.
    The cassette should contain the HTML of the bugcrowd.com/programs page.
    """
    harvester = BugcrowdHarvester()

    async with httpx.AsyncClient() as client:
        result = await harvester.fetch_programs(client)

    assert "programs" in result
    assert "metadata" in result

    programs = result["programs"]

    # This assertion depends on the content of the recorded cassette.
    # The manually created cassette will have at least one program.
    assert len(programs) > 0

    first_program = programs[0]
    assert "external_id" in first_program
    assert "name" in first_program
    assert "program_url" in first_program
    assert "min_payout" in first_program
    assert "max_payout" in first_program
    assert first_program["platform_name"] == "Bugcrowd"
    assert first_program["name"] == "Example Program" # From manual cassette
    assert first_program["min_payout"] == 100
    assert first_program["max_payout"] == 5000
