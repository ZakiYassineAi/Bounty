import os
import pytest
from bounty_command_center.harvesters.intigriti import IntigritiHarvester

pytestmark = pytest.mark.skipif(
    not os.getenv("INTIGRITI_API_KEY"),
    reason="Integration test skipped: no INTIGRITI_API_KEY env var set.",
)

def test_intigriti_live_list_programs():
    """
    This is an integration test that runs against the live Intigriti API.
    It will only run if the INTIGRITI_API_KEY environment variable is set.
    """
    # The default harvester will use the IntigritiClient with the default
    # settings, which reads the API key from the environment.
    harvester = IntigritiHarvester()
    data, etag, last_modified = harvester.fetch_raw_data()

    assert data is not None
    assert isinstance(data, str)
    assert etag is not None
    assert last_modified is not None
