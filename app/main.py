from fastapi import FastAPI
from fastapi.routing import APIRouter
from app.routes import auth

app = FastAPI(title="ExamGenie API")
api_router = APIRouter(prefix="/api")

@app.get("/")
def root() -> dict[str, str]:
    return {"message": "ExamGenie API is running"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


api_router.include_router(auth.router, prefix="/auth", tags=["auth"])


app.include_router(api_router)