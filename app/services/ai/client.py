from openai import OpenAI

from app.common.config import require_env

client = OpenAI(api_key=require_env("OPENAI_API_KEY"))

def get_client():
    return client
