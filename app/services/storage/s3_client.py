import boto3

from app.common.config import require_env

def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=require_env("S3_ENDPOINT_URL"),
        aws_access_key_id=require_env("S3_ACCESS_KEY_ID"),
        aws_secret_access_key=require_env("S3_SECRET_ACCESS_KEY"),
        region_name=require_env("S3_REGION"),
    )
