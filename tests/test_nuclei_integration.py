import asyncio
import json
import pytest
import shlex
from unittest.mock import patch, AsyncMock

import pytest
from sqlmodel import Session, SQLModel, create_engine

from bounty_command_center.models import Target
from bounty_command_center.nuclei_runner import NucleiRunner

# Sample Nuclei JSONL output for mocking
MOCK_NUCLEI_OUTPUT = """
{"template-id":"git-config","info":{"name":"Git Config File","author":["geeknik"],"tags":["git","config","exposure"],"severity":"info"},"matcher-name":"word","type":"http","host":"http://example.com/.git/config","matched-at":"http://example.com/.git/config","ip":"1.2.3.4"}
{"template-id":"exposed-panel","info":{"name":"Some Exposed Panel","author":["hacker"],"tags":["panel","exposure"],"severity":"high"},"matcher-name":"status","type":"http","host":"http://example.com/panel","matched-at":"http://example.com/panel","ip":"1.2.3.4"}
"""

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.mark.asyncio
async def test_nuclei_runner_success(session: Session):
    """
    Test the NucleiRunner with a successful scan and valid output.
    """
    mock_process = AsyncMock()
    mock_process.communicate.return_value = (MOCK_NUCLEI_OUTPUT.encode(), b"")
    mock_process.returncode = 0

    with patch("asyncio.create_subprocess_shell", return_value=mock_process) as mock_shell:
        test_target = Target(name="example.com", url="http://example.com", scope=["http://example.com"])
        session.add(test_target)
        session.commit()

        runner = NucleiRunner()
        findings = await runner.run(test_target)

        mock_shell.assert_called_once()
        called_command = mock_shell.call_args[0][0]
        assert f"-target {shlex.quote(test_target.url)}" in called_command

        assert len(findings) == 2
        assert findings[0].finding_summary == "Git Config File"
        assert findings[1].severity == "High"

@pytest.mark.asyncio
async def test_nuclei_runner_failure(session: Session):
    """
    Test the NucleiRunner when the nuclei command fails.
    """
    mock_process = AsyncMock()
    mock_process.communicate.return_value = (b"", b"Error: target not responding")
    mock_process.returncode = 1

    with patch("asyncio.create_subprocess_shell", return_value=mock_process):
        test_target = Target(name="fail.com", url="http://fail.com", scope=["http://fail.com"])
        session.add(test_target)
        session.commit()

        runner = NucleiRunner()
        findings = await runner.run(test_target)

        assert len(findings) == 0

@pytest.mark.asyncio
async def test_nuclei_runner_command_injection(session: Session):
    """
    Test that the NucleiRunner correctly sanitizes input to prevent command injection.
    """
    mock_process = AsyncMock()
    mock_process.communicate.return_value = (b"", b"") # We don't care about output for this test

    with patch("asyncio.create_subprocess_shell", return_value=mock_process) as mock_shell:
        # URL with a command injection attempt
        malicious_url = "http://example.com; ls -la"
        test_target = Target(name="bad.com", url=malicious_url, scope=[])
        session.add(test_target)
        session.commit()

        runner = NucleiRunner()
        await runner.run(test_target)

        # Assert that the shell command was called
        mock_shell.assert_called_once()
        # Get the actual command string passed to the shell
        called_command = mock_shell.call_args[0][0]

        # Assert that the malicious part is safely quoted and not a separate command
        assert shlex.quote(malicious_url) in called_command
