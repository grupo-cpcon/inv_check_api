import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import INITIALIZED_TENANTS, create_test_app

@pytest.fixture(autouse=True)
def clear_initialized_tenants():
    INITIALIZED_TENANTS.clear()

@pytest.fixture
def mock_mongo():
    with patch("app.core.database.MongoConnection.get_client") as mock:
        client = MagicMock()
        client.list_database_names = AsyncMock(return_value=["tenant_test"])

        db = MagicMock()
        db.name = "tenant_test"
        client.get_database.return_value = db

        mock.return_value = client
        yield

@pytest.fixture
def client(mock_mongo):
    app = create_test_app()
    return TestClient(app)
