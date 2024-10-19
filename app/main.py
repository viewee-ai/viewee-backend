from fastapi import FastAPI, Depends
from .auth.clerk_jwt import get_current_user # https://github.com/clerk/clerk-sdk-python/blob/main/README.md
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# This will allow the frontend to make HTTP requests to the backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # http://localhost:3000
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the GetCooked AI backend!"}

@app.get("/protected")
def protected_route(current_user=Depends(get_current_user)):
    return {"message": "Welcome, you are authenticated!", "user": current_user}

@app.get("/public")
def public_route():
    return {"message": "Welcome to the public API route!"}
