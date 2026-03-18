from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.models import LoginRequest, UserCreate
from app.auth.password import hash_password, verify_password
from app.auth.jwt_handler import create_access_token


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register(self, payload: UserCreate) -> str:
        existing = self.db.query(User).filter(User.email == payload.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        user = User(
            username=payload.username,
            email=payload.email,
            hashed_password=hash_password(payload.password)
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return "Registered! Please login"

    def login(self, payload: LoginRequest) -> dict:
        user = self.db.query(User).filter(User.email == payload.email).first()
        if not user or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        token = create_access_token({"sub": str(user.id)})
        return {"access_token": token, "token_type": "bearer"}