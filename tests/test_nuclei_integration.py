import asyncio
import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from sqlmodel import Session, SQLModel, create_engine
from bounty_command_center.models import Target, Evidence
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
    # 1. Arrange
    # Create a mock process to simulate Nuclei execution
    mock_process = AsyncMock()
    mock_process.communicate.return_value = (MOCK_NUCLEI_OUTPUT.encode(), b"")
    mock_process.returncode = 0

    # Patch asyncio.create_subprocess_exec to return our mock process
    with patch("asyncio.create_subprocess_exec", return_value=mock_process) as mock_exec:
        # Create a test target
        test_target = Target(name="example.com", url="http://example.com")
        session.add(test_target)
        session.commit()

        # 2. Act
        runner = NucleiRunner()
        findings = await runner.run(test_target)

        # 3. Assert
        # Check that nuclei was called correctly
        mock_exec.assert_called_once()
        called_command = mock_exec.call_args[0]
        assert "nuclei" in called_command
        assert "-target" in called_command
        assert test_target.url in called_command
        assert "-jsonl" in called_command

        # Check that the output was parsed correctly
        assert len(findings) == 2

        # Check the details of the first finding (info severity)
        info_finding = findings[0]
        assert info_finding.finding_summary == "Git Config File"
        assert info_finding.severity == "Info"
        assert '"template-id": "git-config"' in info_finding.reproduction_steps

        # Check the details of the second finding (high severity)
        high_finding = findings[1]
        assert high_finding.finding_summary == "Some Exposed Panel"
        assert high_finding.severity == "High"
        assert '"template-id": "exposed-panel"' in high_finding.reproduction_steps

@pytest.mark.asyncio
async def test_nuclei_runner_failure(session: Session):
    """
    Test the NucleiRunner when the nuclei command fails.
    """
    # 1. Arrange
    mock_process = AsyncMock()
    mock_process.communicate.return_value = (b"", b"Error: target not responding")
    mock_process.returncode = 1

    with patch("asyncio.create_subprocess_exec", return_value=mock_process):
        test_target = Target(name="fail.com", url="http://fail.com")
        session.add(test_target)
        session.commit()

        # 2. Act
        runner = NucleiRunner()
        findings = await runner.run(test_target)

        # 3. Assert
        # No evidence should be returned on failure
        assert len(findings) == 0
