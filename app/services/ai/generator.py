from .client import get_client
from .prompts import build_question_prompt 

import random
# def generate_questions(subject, topic , difficulty, num_questions):

#     client = get_client()

#     prompt= build_question_prompt(subject, topic, difficulty, num_questions)
#     response = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[
#             {"role": "user", "content": prompt}
#         ]
#     )

#     return response.choices[0].message.content

def generate_questions(subject, topic, difficulty, num_questions):

    questions = []

    for i in range(num_questions):
        correct = random.choice(["A", "B", "C", "D"])

        question = {
            "question": f"{subject} question {i+1} on {topic} ({difficulty})",
            "options": {
                "A": f"Option A for question {i+1}",
                "B": f"Option B for question {i+1}",
                "C": f"Option C for question {i+1}",
                "D": f"Option D for question {i+1}"
            },
            "correct_answer": correct,
            "explanation": f"This is a sample explanation for question {i+1}"
        }

        questions.append(question)

    return {"questions": questions}