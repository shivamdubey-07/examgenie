from jose import jwt, JWTError
from fastapi import HTTPException, status
from datetime import datetime, timedelta

from app.common.config import require_env

SECRET_KEY = require_env("JWT_SECRET_KEY")
ALGORITHM = require_env("JWT_ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(require_env("TOKEN_EXPIRE_MINUTES"))


def create_access_token(data: dict):

    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired or invalid"
        )