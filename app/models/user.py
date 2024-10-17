from pydantic import BaseModel, EmailStr

class UserResponse(BaseModel):
    id: str  # Clerk's user ID (string format)
    email: EmailStr

    class Config:
        orm_mode = True
