import pytest
import vcr
import requests
import respx
import httpx
import json
from unittest.mock import MagicMock
from bounty_command_center.harvesters.intigriti import IntigritiHarvester, IntigritiClient
from bounty_command_center.harvesters.yeswehack import YesWeHackHarvester
from bounty_command_center.harvesters.openbugbounty import OpenBugBountyHarvester

@respx.mock
def test_intigriti_fetch_raw_data_with_mock():
    """
    Tests the IntigritiHarvester using a respx mock.
    This test does not require a network connection or a real API key.
    """
    # Arrange
    api_url = "https://api.intigriti.com/external/company/v2.0/programs"
    mock_response_data = [{"id": "p1", "name": "Alpha", "status": "active"}]

    route = respx.get(api_url).mock(
        return_value=httpx.Response(
            200,
            json=mock_response_data,
            headers={"ETag": "new-etag", "Last-Modified": "a-new-date"}
        )
    )

    # We inject a client that uses the mocked transport
    fake_client = IntigritiClient(api_key_provider=lambda: "FAKE_KEY")
    harvester = IntigritiHarvester(client=fake_client)

    # Act
    data, etag, last_modified = harvester.fetch_raw_data()

    # Assert
    assert route.called
    assert json.loads(data) == mock_response_data
    assert etag == "new-etag"
    assert last_modified == "a-new-date"


# We now use record_mode='once' (the default) since the cassettes are fresh.
@vcr.use_cassette("tests/cassettes/public/test_yeswehack_fetch_raw_data_success.yaml")
def test_yeswehack_fetch_raw_data_success():
    """
    Tests that the YesWeHackHarvester can successfully fetch and return raw data.
    """
    harvester = YesWeHackHarvester()
    data, etag, last_modified = harvester.fetch_raw_data()
    assert data is not None
    assert "<title>" in data

@vcr.use_cassette("tests/cassettes/public/test_openbugbounty_fetch_raw_data_success.yaml")
def test_openbugbounty_fetch_raw_data_success():
    """
    Tests that the OpenBugBountyHarvester can successfully fetch and return raw data.
    """
    harvester = OpenBugBountyHarvester()
    data, etag, last_modified = harvester.fetch_raw_data()
    assert data is not None
    assert "Bug Bounty Program List" in data

def test_intigriti_handles_request_exception(mocker):
    """
    Tests that the IntigritiHarvester handles network errors gracefully.
    """
    # Mock the client's list_programs method directly
    mock_client = MagicMock()
    mock_client.list_programs.side_effect = httpx.RequestError("Network error")
    harvester = IntigritiHarvester(client=mock_client)

    data, etag, last_modified = harvester.fetch_raw_data()

    assert data is None
    assert etag is None
    assert last_modified is None
