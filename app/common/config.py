import os

from dotenv import load_dotenv


load_dotenv()


def require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value == "":
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        return url

    db_user = require_env("POSTGRES_USER")
    db_pass = require_env("POSTGRES_PASSWORD")
    db_host = require_env("DB_HOST")
    db_port = require_env("DB_PORT")
    db_name = require_env("POSTGRES_DB")
    return f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
