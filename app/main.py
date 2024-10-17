from fastapi import FastAPI
from app.routers import users, interview

app = FastAPI(
    title="Technical Interview Simulator",
    description="",
    version="1.0.0",
)

# Include the routers for modular handling
app.include_router(users.router)
app.include_router(interview.router)

@app.get("/")
def root():
    return {"message": "Welcome to the AI Interview Simulator"}
