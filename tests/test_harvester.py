import pytest
import os
import httpx
from bounty_command_center.harvester.hackerone_harvester import HackeroneHarvester

@pytest.mark.vcr
async def test_hackerone_harvester_fetch():
    """
    Tests the HackeroneHarvester's fetch_programs method.
    This test uses VCR.py to record and replay the interaction with the H1 API.
    To record a new cassette, you must have H1_USER and H1_TOKEN environment
    variables set with valid credentials.
    """
    # Temporarily set credentials from more securely named env vars for recording.
    # These will NOT be saved in the cassette file due to the filter in conftest.py
    original_user = os.getenv("HACKERONE_USERNAME")
    original_token = os.getenv("HACKERONE_API_TOKEN")

    # Use test-specific env vars if available, otherwise use dummy values
    os.environ['HACKERONE_USERNAME'] = os.getenv('H1_USER', 'test-user-for-vcr')
    os.environ['HACKERONE_API_TOKEN'] = os.getenv('H1_TOKEN', 'test-token-for-vcr')

    try:
        harvester = HackeroneHarvester()
        async with httpx.AsyncClient() as client:
            result = await harvester.fetch_programs(client)
    finally:
        # Restore original environment variables
        if original_user is None:
            del os.environ['HACKERONE_USERNAME']
        else:
            os.environ['HACKERONE_USERNAME'] = original_user

        if original_token is None:
            del os.environ['HACKERONE_API_TOKEN']
        else:
            os.environ['HACKERONE_API_TOKEN'] = original_token

    assert "programs" in result
    assert "metadata" in result

    # This assertion depends on the content of the recorded cassette.
    # When running against a pre-recorded cassette, it should be deterministic.
    # For now, we can check that the structure is correct.
    assert isinstance(result["programs"], list)

    if result["programs"]:
        first_program = result["programs"][0]
        assert "external_id" in first_program
        assert "name" in first_program
        assert "program_url" in first_program
        assert first_program["platform_name"] == "HackerOne"
