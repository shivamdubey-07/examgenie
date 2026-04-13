from openai import OpenAI

from app.common.config import require_env

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=require_env("HF_TOKEN"),
)
# OpenAI(api_key=require_env("OPENAI_API_KEY"))

def get_client():
    return client
