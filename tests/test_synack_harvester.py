import pytest
import asyncio
import json
from unittest.mock import MagicMock, AsyncMock

from bounty_command_center.harvesters.synack import SynackHarvester

@pytest.fixture
def mock_playwright(mocker):
    """A fixture to provide a fully mocked playwright environment."""
    mock_page = AsyncMock()
    mock_context = AsyncMock()
    mock_context.new_page.return_value = mock_page
    mock_browser = AsyncMock()
    mock_browser.new_context.return_value = mock_context

    pw_manager = AsyncMock()
    pw_manager.__aenter__.return_value.chromium.launch.return_value = mock_browser

    mocker.patch("bounty_command_center.harvesters.synack.async_playwright", return_value=pw_manager)

    return {
        "page": mock_page,
        "context": mock_context,
        "browser": mock_browser,
        "pw_manager": pw_manager
    }

@pytest.mark.asyncio
async def test_synack_harvester_with_existing_auth(mocker, mock_playwright):
    """
    Tests the SynackHarvester's success path when an auth file already exists.
    """
    mocker.patch("pathlib.Path.exists", return_value=True)
    mock_playwright["page"].url = "https://platform.synack.com/tasks"

    harvester = SynackHarvester()
    data, _, _ = await harvester.fetch_raw_data()

    mock_playwright["browser"].new_context.assert_awaited_with(storage_state=str(harvester.AUTH_FILE))
    parsed_data = json.loads(data)
    assert parsed_data[0]["name"] == "Dummy Synack Program"

@pytest.mark.asyncio
async def test_synack_harvester_needs_login_success(mocker, mock_playwright):
    """
    Tests the logic for a successful manual login.
    """
    mocker.patch("pathlib.Path.exists", return_value=False)
    mock_playwright["page"].url = "https://platform.synack.com/login"

    # In the success case, wait_for_url should complete instantly,
    # while wait_for_selector should hang until cancelled.
    async def long_wait(*args, **kwargs):
        await asyncio.sleep(10)

    mock_playwright["page"].wait_for_url.return_value = asyncio.Future()
    mock_playwright["page"].wait_for_url.return_value.set_result(True)
    mock_playwright["page"].wait_for_selector.side_effect = long_wait

    harvester = SynackHarvester()
    await harvester.fetch_raw_data()

    mock_playwright["browser"].new_context.assert_any_await()
    mock_playwright["context"].storage_state.assert_awaited()

@pytest.mark.asyncio
async def test_synack_harvester_fails_on_captcha(mocker, mock_playwright, capsys):
    """
    Tests that the harvester fails gracefully if a CAPTCHA is detected.
    """
    mocker.patch("pathlib.Path.exists", return_value=False)
    mock_playwright["page"].url = "https://platform.synack.com/login"

    # In the CAPTCHA case, wait_for_selector should complete instantly,
    # while wait_for_url should hang until cancelled.
    async def long_wait(*args, **kwargs):
        await asyncio.sleep(10)

    mock_playwright["page"].wait_for_selector.side_effect = None
    mock_playwright["page"].wait_for_selector.return_value = asyncio.Future()
    mock_playwright["page"].wait_for_selector.return_value.set_result(True)
    mock_playwright["page"].wait_for_url.side_effect = long_wait

    harvester = SynackHarvester()
    result = await harvester.fetch_raw_data()

    assert result == (None, None, None)
    captured = capsys.readouterr()
    assert "CAPTCHA detected" in captured.out

@pytest.mark.asyncio
async def test_synack_harvester_retry_logic_succeeds(mocker, mock_playwright):
    """
    Tests that the harvester succeeds even if a transient error occurs.
    """
    mocker.patch("pathlib.Path.exists", return_value=True)
    mock_playwright["page"].url = "https://platform.synack.com/tasks"

    mock_playwright["page"].goto.side_effect = [
        asyncio.TimeoutError("Network failed on first attempt"),
        AsyncMock(),
        AsyncMock(),
    ]

    harvester = SynackHarvester()
    data, _, _ = await harvester.fetch_raw_data()

    assert mock_playwright["page"].goto.await_count > 1
    assert data is not None
    parsed_data = json.loads(data)
    assert parsed_data[0]["name"] == "Dummy Synack Program"
