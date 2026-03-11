def build_question_prompt(subject, topic, difficulty, num_questions):

    return f"""
You are an exam question generator.

Generate {num_questions} multiple choice questions.

Subject: {subject}
Topic: {topic}
Difficulty: {difficulty}

Return STRICT JSON format:

{{
 "questions":[
  {{
   "question":"",
   "options": {{
      "A":"",
      "B":"",
      "C":"",
      "D":""
   }},
   "correct_answer":"",
   "explanation":""
  }}
 ]
}}

Do not add text outside JSON.
"""