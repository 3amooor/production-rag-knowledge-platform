"""S3-compatible object storage boundary for document originals."""

from uuid import UUID, uuid4

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import get_settings


class StorageError(RuntimeError):
    """Raised when the configured object store cannot complete an operation."""


def get_storage_client():
    settings = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=settings.object_storage_endpoint,
        aws_access_key_id=settings.minio_root_user,
        aws_secret_access_key=settings.minio_root_password,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def create_document_key(workspace_id: UUID, document_id: UUID) -> str:
    return f"workspaces/{workspace_id}/documents/{document_id}/versions/{uuid4()}"


def put_document(key: str, data: bytes, content_type: str) -> None:
    client = get_storage_client()
    bucket = get_settings().object_storage_bucket
    try:
        client.head_bucket(Bucket=bucket)
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") not in {"404", "NoSuchBucket"}:
            raise StorageError("Object storage bucket is not accessible.") from exc
        try:
            client.create_bucket(Bucket=bucket)
        except ClientError as create_exc:
            if create_exc.response.get("Error", {}).get("Code") != "BucketAlreadyOwnedByYou":
                raise StorageError("Could not create object storage bucket.") from create_exc
    try:
        client.put_object(Bucket=bucket, Key=key, Body=data, ContentType=content_type)
    except (BotoCoreError, ClientError) as exc:
        raise StorageError("Could not store document.") from exc


def get_document(key: str) -> bytes:
    """Read a document original from the configured tenant-safe key."""

    try:
        response = get_storage_client().get_object(
            Bucket=get_settings().object_storage_bucket, Key=key
        )
        return response["Body"].read()
    except (BotoCoreError, ClientError) as exc:
        raise StorageError("Could not read document.") from exc
