import requests
from jose import JWTError, jwt
from fastapi import HTTPException, Depends, Request

CLERK_JWKS_URL = "https://your-clerk-domain/.well-known/jwks.json"
CLERK_ISSUER = "https://your-clerk-domain"

def get_public_key():
    """
    Fetches the Clerk JWKS (JSON Web Key Set) for verifying the JWT signature.
    """
    response = requests.get(CLERK_JWKS_URL)
    if response.status_code != 200:
        raise Exception("Could not fetch Clerk JWKS")
    return response.json()

def verify_clerk_token(token: str):
    """
    Verifies the Clerk-issued JWT token and returns the decoded payload if valid.
    """
    public_keys = get_public_key()
    try:
        # Decode and verify the token
        payload = jwt.decode(
            token,
            public_keys,
            algorithms=["RS256"],
            audience=CLERK_ISSUER,
            issuer=CLERK_ISSUER,
        )
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(request: Request):
    """
    Retrieves the current user based on the Clerk token in the Authorization header.
    """
    authorization: str = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing or invalid")
    
    token = authorization.split(" ")[1]
    return verify_clerk_token(token)