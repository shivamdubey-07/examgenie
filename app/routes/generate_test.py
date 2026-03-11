from fastapi import APIRouter
from app.services.ai.generator import generate_questions
from app.schemas.test_schema import TestRequest, TestResponse

router = APIRouter()

@router.post("/generate-test", response_model=TestResponse)
def generate_test(data : TestRequest):
    questions=generate_questions(
        data.subject,
        data.topic,
        data.difficulty,
        data.num_questions
    )
    return questions