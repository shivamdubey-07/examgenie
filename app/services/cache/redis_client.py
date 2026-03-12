import redis

from app.common.config import require_env

def get_redis_client() -> redis.Redis:
    url = require_env("REDIS_URL")
    return redis.Redis.from_url(url, decode_responses=True)
