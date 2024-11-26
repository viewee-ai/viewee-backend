import pytest
from unittest.mock import patch, MagicMock
from app.main import startup_db_client, shutdown_db_client, app

@patch("app.main.AsyncIOMotorClient")
@pytest.mark.asyncio
async def test_startup_db_client(mock_motor_client):
    mock_client = MagicMock()
    mock_motor_client.return_value = mock_client

    await startup_db_client()

    mock_motor_client.assert_called_once()
    assert hasattr(app, "mongodb_client")

@patch("app.main.AsyncIOMotorClient")
@pytest.mark.asyncio
async def test_shutdown_db_client(mock_motor_client):
    mock_client = MagicMock()
    mock_motor_client.return_value = mock_client
    app.mongodb_client = mock_client

    await shutdown_db_client()

    mock_client.close.assert_called_once()
