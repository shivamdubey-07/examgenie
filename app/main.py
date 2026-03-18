from fastapi import FastAPI
from fastapi.routing import APIRouter
from app.routes import auth
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="ExamGenie API")
api_router = APIRouter(prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "ExamGenie API is running"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


api_router.include_router(auth.router, prefix="/auth", tags=["auth"])


app.include_router(api_router)