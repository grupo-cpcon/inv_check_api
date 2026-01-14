from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient
import pytest
from app.main import create_test_app

def test_missing_tenant_header():
    app = create_test_app()
    client = TestClient(app)

    with pytest.raises(HTTPException) as exc:
        client.get("/load")

    assert exc.value.status_code == 400
    assert exc.value.detail == "Header 'tenant' é obrigatório"

def test_tenant_not_found():
    with patch("app.core.database.MongoConnection.get_client") as mock:
        client_mongo = MagicMock()
        client_mongo.list_database_names = AsyncMock(return_value=[])
        mock.return_value = client_mongo

        app = create_test_app()
        client_http = TestClient(app)

        with pytest.raises(HTTPException) as exc:
            client_http.get("/load", headers={"tenant": "invalido"})

        assert exc.value.status_code == 404
