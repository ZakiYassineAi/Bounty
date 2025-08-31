import pytest
from bounty_command_center.harvesters.intigriti import IntigritiHarvester
from bounty_command_center.harvesters.yeswehack import YesWeHackHarvester
from bounty_command_center.harvesters.openbugbounty import OpenBugBountyHarvester

def test_intigriti_fetch_raw_data_success(mocker):
    """
    Tests that fetch_raw_data returns the raw JSON string on success.
    """
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.text = '{"programs": []}'
    mocker.patch('requests.get', return_value=mock_response)

    harvester = IntigritiHarvester(api_key="dummy_api_key")
    raw_data = harvester.fetch_raw_data()
    assert raw_data is not None
    assert isinstance(raw_data, str)
    assert raw_data == '{"programs": []}'

def test_intigriti_fetch_raw_data_no_api_key():
    """
    Tests that fetch_raw_data raises a ValueError if no API key is provided.
    """
    harvester = IntigritiHarvester(api_key=None)
    with pytest.raises(ValueError):
        harvester.fetch_raw_data()

@pytest.mark.vcr()
def test_yeswehack_fetch_raw_data_success():
    """
    Tests that fetch_raw_data returns the raw HTML string on success.
    """
    harvester = YesWeHackHarvester()
    raw_data = harvester.fetch_raw_data()
    assert raw_data is not None
    assert isinstance(raw_data, str)

@pytest.mark.vcr()
def test_openbugbounty_fetch_raw_data_success():
    """
    Tests that fetch_raw_data returns the raw HTML string on success.
    """
    harvester = OpenBugBountyHarvester()
    raw_data = harvester.fetch_raw_data()
    assert raw_data is not None
    assert isinstance(raw_data, str)
