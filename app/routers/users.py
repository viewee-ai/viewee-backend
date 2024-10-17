from fastapi import APIRouter, Depends, HTTPException, Request
from app.models.user import UserResponse
from app.auth.clerk_jwt import get_current_user

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """
    Fetch the current user's profile information.
    The current_user is the decoded Clerk JWT payload.
    """
    return UserResponse(
        id=current_user["sub"],  # Clerk user ID
        email=current_user["email"]
    )
