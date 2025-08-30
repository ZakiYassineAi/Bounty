import pytest

@pytest.fixture(scope='module')
def vcr_config():
    return {
        # Replace the Authorization header with a dummy value to avoid storing secrets in cassettes
        "filter_headers": [('authorization', 'DUMMY')],
        # Where to store the cassettes
        "cassette_library_dir": "tests/fixtures/cassettes",
    }
