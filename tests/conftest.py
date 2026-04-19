import pytest
from travel import TravelClient

@pytest.fixture
async def client():
    """Shared TravelClient instance for tests, function scoped to prevent loop issues."""
    async with TravelClient(verbose=False) as c:
        yield c
