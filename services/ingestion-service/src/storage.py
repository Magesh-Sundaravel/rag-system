import boto3

from src.config import settings


def _client():
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url or None,
        region_name=settings.aws_region,
    )


def upload_raw(key: str, data: bytes, content_type: str) -> str:
    """Push the raw upload to S3 (services keep no local files). Returns the s3:// URI."""
    _client().put_object(Bucket=settings.s3_bucket, Key=key, Body=data, ContentType=content_type)
    return f"s3://{settings.s3_bucket}/{key}"
