import pytest
from sqlmodel import Session, create_engine, SQLModel
from bounty_command_center import models

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(autouse=True)
def nonetwork(monkeypatch):
    # احظر أي اتصالات شبكية حية في CI، استخدم VCR/Mocks بدلًا منها.
    pass
