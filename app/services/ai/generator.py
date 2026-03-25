from .client import get_client
from .prompts import build_question_prompt
import json
import logging

logger = logging.getLogger(__name__)


def generate_questions(subject: str, topic: str, difficulty: str, num_questions: int) -> dict:
    """
    Generate multiple choice questions using OpenAI API.
    
    :param subject: Exam subject
    :param topic: Exam topic
    :param difficulty: Difficulty level (easy, medium, hard)
    :param num_questions: Number of questions to generate
    :return: Dict with 'questions' list
    :raises: ValueError if response parsing fails
    """
    client = get_client()
    prompt = build_question_prompt(subject, topic, difficulty, num_questions)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        response_text = response.choices[0].message.content
        
        # Parse JSON response
        questions_data = json.loads(response_text)
        
        # Validate structure
        if "questions" not in questions_data:
            raise ValueError("Response missing 'questions' key")
        
        if not isinstance(questions_data["questions"], list):
            raise ValueError("'questions' must be a list")
        
        if len(questions_data["questions"]) == 0:
            raise ValueError("No questions generated")
        
        # Validate each question structure
        for idx, q in enumerate(questions_data["questions"]):
            _validate_question_structure(q, idx)
        
        logger.info(f"Successfully generated {len(questions_data['questions'])} questions")
        return questions_data

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse OpenAI response as JSON: {e}")
        raise ValueError(f"Invalid JSON response from AI: {e}")
    except Exception as e:
        logger.error(f"Error generating questions: {e}")
        raise


def _validate_question_structure(question: dict, index: int) -> None:
    """Validate a single question has required fields."""
    required_fields = ["question", "options", "correct_answer", "explanation"]
    for field in required_fields:
        if field not in question:
            raise ValueError(f"Question {index} missing required field: {field}")
    
    # Validate options is a dict with A, B, C, D keys
    options = question["options"]
    if not isinstance(options, dict):
        raise ValueError(f"Question {index}: options must be a dict")
    
    required_option_keys = {"A", "B", "C", "D"}
    if not required_option_keys.issubset(set(options.keys())):
        raise ValueError(f"Question {index}: must have options A, B, C, D")
    
    # Validate correct_answer is one of A, B, C, D
    correct = question["correct_answer"]
    if correct not in required_option_keys:
        raise ValueError(f"Question {index}: correct_answer must be one of A, B, C, D, got {correct}")