from fastapi import FastAPI
from fastapi.routing import APIRouter
from app.routes import auth, exam, attempts

app = FastAPI(title="ExamGenie API")
api_router = APIRouter(prefix="/api")


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "ExamGenie API is running"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(exam.router, prefix="/exam", tags=["exam"])
api_router.include_router(attempts.router, prefix="/attempts", tags=["attempts"])


app.include_router(api_router)