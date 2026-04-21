from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.models import LoginRequest, UserCreate
from app.services.auth.auth_service import AuthService
from app.auth.dependencies import get_current_user
from app.auth.jwt_handler import verify_token, create_access_token, TokenType
from app.models.user import User

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    service = AuthService(db)
    return service.register(payload)


@router.post("/login", status_code=status.HTTP_200_OK)
def login(
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    service = AuthService(db)
    return service.login(payload, response)


@router.post("/refresh", status_code=status.HTTP_200_OK)
def refresh_token(request: Request):
    """
    Frontend calls this when access token expires.
    Reads refresh token from httpOnly cookie, returns new access token.
    """
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token found. Please login again."
        )

    payload = verify_token(token, expected_type=TokenType.refresh)
    new_access_token = create_access_token({"sub": payload["sub"]})

    return {"access_token": new_access_token, "token_type": "bearer"}


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(response: Response):
    """
    Clears the refresh token cookie.
    Frontend should also clear its access token from memory.
    """
    response.delete_cookie(
        key="refresh_token",
        path="/api/auth/refresh",
        httponly=True,
        secure=False,   # Match what was set in login
        samesite="lax",
    )
    return {"message": "Logged out successfully"}


@router.get("/me", status_code=status.HTTP_200_OK)
def get_me(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Verify the current access token is valid and return user info.
    Frontend calls this on app load to check if user is still logged in.
    """
    user = (
        db.query(User)
        .filter(User.id == UUID(current_user["sub"]))
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "name": user.name,
        "role": user.role.value,
    }