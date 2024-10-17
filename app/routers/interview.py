from fastapi import APIRouter, WebSocket
from app.services.feedback_service import provide_real_time_feedback

router = APIRouter(
    prefix="/interview",
    tags=["interview"],
)

@router.websocket("/code-session")
async def code_session(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Receive code from the client
            data = await websocket.receive_text()
            # Provide real-time feedback on the code
            feedback = provide_real_time_feedback(data)
            # Send feedback to the client
            await websocket.send_text(feedback)
    except Exception as e:
        await websocket.close()
