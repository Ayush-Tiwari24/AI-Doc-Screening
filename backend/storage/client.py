import boto3
from botocore.client import Config

from config import settings


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=f"{'https' if settings.minio_secure else 'http'}://{settings.minio_endpoint}",
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def upload_file(file_path: str, object_name: str) -> str:
    client = get_s3_client()
    client.upload_file(file_path, settings.minio_bucket, object_name)
    return object_name


def get_presigned_url(object_name: str, expires_in: int = 3600) -> str:
    client = get_s3_client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.minio_bucket, "Key": object_name},
        ExpiresIn=expires_in,
    )