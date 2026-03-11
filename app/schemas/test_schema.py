from pydantic import BaseModel
from typing import Dict, List


class TestRequest(BaseModel):
    subject: str
    topic: str
    difficulty: str
    num_questions: int


class Question(BaseModel):
    question: str
    options: Dict[str, str]
    correct_answer: str
    explanation: str


class TestResponse(BaseModel):
    questions: List[Question]