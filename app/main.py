from fastapi import FastAPI
from app.routes import generate_test


app = FastAPI(title="ExamGenie API")

app.include_router(generate_test.router)

def root():
    return {"message": "ExamGenie API is running"}


