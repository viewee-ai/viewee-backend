import pytest
from starlette.testclient import TestClient
from app.main import app, sessions

@pytest.mark.asyncio
def test_websocket_tts():
    # Add a mock session with feedback
    sessions["mock_session"] = {"feedback": "This is a test feedback"}

    with TestClient(app) as client:
        with client.websocket_connect("/ws/tts?session_id=mock_session") as websocket:
            # Receive binary data in chunks
            binary_data = websocket.receive_bytes()
            assert binary_data is not None
            assert len(binary_data) > 0
