from fastapi import HTTPException, status, Response
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.models import LoginRequest, UserCreate
from app.auth.password import hash_password, verify_password
from app.auth.jwt_handler import create_access_token, create_refresh_token


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register(self, payload: UserCreate) -> str:
        existing_email = (
            self.db.query(User).filter(User.email == payload.email).first()
        )
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )

        existing_username = (
            self.db.query(User).filter(User.username == payload.username).first()
        )
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken"
            )

        user = User(
            username=payload.username,
            email=payload.email,
            name=payload.name,
            hashed_password=hash_password(payload.password),
            role=payload.role,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return "Registered successfully. Please login."

    def login(self, payload: LoginRequest, response: Response) -> dict:
        user = (
            self.db.query(User).filter(User.email == payload.email).first()
        )
        if not user or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )

        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = create_refresh_token({"sub": str(user.id)})

        # Refresh token goes in httpOnly cookie — not accessible by JS
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=False,   # Set True in production (requires HTTPS)
            samesite="lax",
            max_age=7 * 24 * 3600,
            path="/api/auth/refresh",
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "name": user.name,
                "role": user.role.value,
            }
        }