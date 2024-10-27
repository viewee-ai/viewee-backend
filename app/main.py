import os
from fastapi import FastAPI, Depends, HTTPException
from .auth.clerk_jwt import get_current_user # https://github.com/clerk/clerk-sdk-python/blob/main/README.md
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Dict, Optional
from uuid import uuid4

load_dotenv()

app = FastAPI()

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Remember to adjust this to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
    
class FeedbackRequest(BaseModel):
    session_id: str
    code: Optional[str] = None
    transcript: Optional[str] = None

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
    session_id = str(uuid4())  # Generate a unique session ID
    sessions[session_id] = {
        "question": question_data.model_dump(),
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
# Route to handle incremental code and transcript updates
@app.post("/api/incremental-feedback")
async def incremental_feedback(request: FeedbackRequest):
    print("Received a request at /api/incremental-feedback")
    print(f"Session ID received: {request.session_id}")

    session = sessions.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    # Update the code and/or transcript in the session
    if request.code:
        print(f"Received code update for session {request.session_id}:\n{request.code}")
        session["code"] = request.code  # Update code in the session
    if request.transcript:
        print(f"Received transcript update for session {request.session_id}:\n{request.transcript}")
        session["transcript"] += f" {request.transcript}"  # Append transcript to the session

    prompt = [
        {"role": "system", "content": "You are a Technical Interviewer. Given the coding challenge, provide feedback to the user based on their current solution and thought process."},
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
        response = client.chat.completions.create(
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
    
################################################################################################################
# Combined route to process both code and transcripts

# @app.post("/api/generate-response")
# async def generate_response(request: CodeRequest, transcript: Optional[str] = None):
    prompt = f"""
    Using the following code and transcript, provide a response as an interviewer:

    Code Question: {request.question}
    Code: {request.code}
    
    Transcript from User: {transcript}
    """
    
    response = openai.Completion.create(
        engine="gpt-4o-mini",
        prompt=prompt,
        max_tokens=300,
        temperature=0.5,
    )
    return {"interviewer_response": response.choices[0].text.strip()}
