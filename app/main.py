import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from .auth.clerk_jwt import get_current_user
from fastapi.middleware.cors import CORSMiddleware
import openai
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Dict, Optional
from uuid import uuid4

import aiohttp
import asyncio


load_dotenv()

app = FastAPI()

openai.api_key = os.environ.get("OPENAI_API_KEY")
deepgram_api_key = os.environ.get("DEEPGRAM_API_KEY")
deepgram_url = "https://api.deepgram.com/v1/speak?model=aura-asteria-en&encoding=mp3"

# CORS setup
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://production.com", 
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
    

@app.get("/")
def read_root():
    return {"message": "Welcome to the GetCooked AI backend!"}

################################################################################################################

@app.get("/protected")
def protected_route(current_user=Depends(get_current_user)):
    return {"message": "Welcome, you are authenticated!", "user": current_user}

################################################################################################################
# Data models for requests
""" class CodeRequest(BaseModel):
    code: str
    question: str

# Handle code evaluation requests
@app.post("/api/evaluate-code")
async def evaluate_code(request: CodeRequest):
    response = openai.Completion.create(
        engine="gpt-4o-mini",
        prompt=f"Evaluate this code for question '{request.question}':\n\n{request.code}",
        max_tokens=150,
        temperature=0.3,
    )
    
    result = response.choices[0].text.strip()
    print(f"Generated code evaluation result: {result}")
    return {"result": response.choices[0].text.strip()} """

################################################################################################################
# Temporary in-memory storage for sessions
sessions: Dict[str, Dict] = {}

class QuestionData(BaseModel):
    title: str
    description: str
    input: str
    output: str
    explanation: Optional[str]
    
@app.post("/api/initialize-question")
async def initialize_question(question_data: QuestionData):
    session_id = str(uuid4()) 
    sessions[session_id] = {
        "question": question_data.dict(),
        "code": "",
        "transcript": "",
        "feedback": ""
    }
    print(f"Initialized session {session_id} with question: {question_data.title}")
    return {"session_id": session_id}

################################################################################################################
# Handle transcript data
""" class TranscriptRequest(BaseModel):
    message: str

@app.post("/api/transcript")
async def handle_transcript(request: TranscriptRequest):
    transcript = request.message
    # TODO: prepare for combination with code evaluation
    # Notify user to check their microphone if the transcript is empty
    print(f"Received transcript: {request.message}")
    return {"message": "Transcript received", "transcript": transcript} """

################################################################################################################
class FeedbackRequest(BaseModel):
    session_id: str
    code: Optional[str] = None
    transcript: Optional[str] = None
    status: str    
    
"""
incremental_feedback: Processes interview feedback requests and generates responses

Data Flow:
1. Validates session and updates session data (code/transcript)
2. Constructs prompt with user's solution and thought process
3. Generates feedback using GPT-4
4. Stores feedback in session for TTS processing
5. Returns feedback response to client

Args:
    request (FeedbackRequest): Contains session_id, code, transcript, and status
Returns:
    dict: Contains generated feedback
"""
@app.post("/api/incremental-feedback")
async def incremental_feedback(request: FeedbackRequest):
    print("Received a request at /api/incremental-feedback")
    print(f"Session ID received: {request.session_id}")

    session = sessions.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    
    if request.status != 'Thinking':
        print("Skipping feedback generation since status is not 'Thinking'")

    # Update the code and/or transcript in the session
    if request.code:
        print(f"Received code update for session {request.session_id}:\n{request.code}")
        session["code"] = request.code 
    if request.transcript:
        print(f"Received transcript update for session {request.session_id}:\n{request.transcript}")
        session["transcript"] += f" {request.transcript}" 

    prompt = [
        {"role": "system", "content": "You are a Technical Interviewer for a Software Engineer role. Given the coding challenge, your task is to faciliate a real technical interview scenario to the user based on their current solution and thought process."},
        {"role": "user", "content": f"""
            Evaluate the following solution for the question '{session['question']['title']}'.

            Description: {session['question']['description']}
            Input: {session['question']['input']}
            Expected Output: {session['question']['output']}
            Explanation: {session['question'].get('explanation', '')}

            user's current code Solution: {session['code']}
            User's Transcript: {session['transcript']}

            Do not provide any type of solutions or hints, only feedback for the user's current solution based on the code and user's thought process.
        """}
    ]

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=prompt,
            max_tokens=150,
            temperature=0.5,
        )
        feedback = response.choices[0].message.content.strip()
        session["feedback"] = feedback
        print(f"Feedback for session {request.session_id}: {feedback}")
        return {"feedback": feedback}
    except Exception as e:
        print("Error generating feedback:", e)
        raise HTTPException(status_code=500, detail="Failed to generate feedback.")

"""
websocket_tts_endpoint: Streams TTS audio for interview feedback in real-time over WebSocket
Note: https://developers.deepgram.com/docs/streaming-text-to-speech

Data Flow:
1. Accept WebSocket Connection: The WebSocket connection is accepted.
2. Retrieve Session Data: Fetches the session data, including the feedback text, based on session_id.
3. TTS API Request: Sends the feedback text to the Deepgram API for TTS conversion, with response headers expecting binary audio data (audio/mpeg format).
4. Chunked Audio Streaming: Reads the Deepgram API response in 1024-byte chunks and streams each 5. chunk over the WebSocket using websocket.send_bytes(chunk).
5. Handle Disconnects: If the WebSocket disconnects, stops streaming and closes the connection.

Args:
    websocket (WebSocket): Client WebSocket connection
    session_id (str): Session identifier for feedback retrieval
"""
@app.websocket("/ws/tts")
async def websocket_tts_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    
    session = sessions.get(session_id)
    if not session or "feedback" not in session:
        await websocket.close(code=1000, reason="No feedback available for this session.")
        return

    feedback_text = session["feedback"]
    
    headers = {
        "Authorization": f"Token {deepgram_api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {"text": feedback_text}

    async with aiohttp.ClientSession() as session:
        async with session.post(deepgram_url, headers=headers, json=payload, timeout=None) as response:
            
            print(f"Response Status: {response.status}")
            print(f"Response Headers: {response.headers}")
            if response.headers.get("Content-Type") not in ["audio/mpeg", "audio/wav"]:
                print("Unexpected content-type received. Expected binary audio data.")
                await websocket.close(code=1003, reason="Unexpected content-type")
                return
            
            try:
                # Stream response chunks to the WebSocket client
                async for chunk in response.content.iter_chunked(1024):
                    if chunk:
                        print(f"Sending audio chunk of size {len(chunk)} bytes.")
                        await websocket.send_bytes(chunk)
            except WebSocketDisconnect:
                print("WebSocket disconnected.")
            except Exception as e:
                print(f"Error in streaming audio data: {e}")
            finally:
                await websocket.close()

    print("TTS streaming complete.")
    
################################################################################################################
# Combined route to process both code and transcripts

# @app.post("/api/generate-response")
# async def generate_response(request: CodeRequest, transcript: Optional[str] = None):
    #prompt = f"""
    #Using the following code and transcript, provide a response as an interviewer:

    #Code Question: {request.question}
    #Code: {request.code}
    
    #Transcript from User: {transcript}
    #"""
    
    #response = openai.Completion.create(
    #    engine="gpt-4o-mini",
    #    prompt=prompt,
    #    max_tokens=300,
    #    temperature=0.5,
    #)
    #return {"interviewer_response": response.choices[0].text.strip()}

