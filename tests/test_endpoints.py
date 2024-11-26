import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app, sessions

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the GetCooked AI backend!"}

def test_initialize_question():
    response = client.post(
        "/api/initialize-question",
        json={
            "title": "Sample Question",
            "description": "Describe the problem.",
            "input": "Sample input",
            "output": "Sample output",
            "explanation": "Explain solution."
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data

@pytest.mark.asyncio
@patch("app.main.openai.ChatCompletion.create")
async def test_incremental_feedback(mock_openai):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Mock feedback"
    mock_openai.return_value = mock_response

    sessions["mock_session"] = {
        "question": {"title": "Test Question", "description": "", "input": "", "output": ""},
        "code": "",
        "transcript": "",
        "feedback": ""
    }

    response = client.post(
        "/api/incremental-feedback",
        json={"session_id": "mock_session", "status": "Thinking"}
    )
    assert response.status_code == 200
    assert response.json()["feedback"] == "Mock feedback"
