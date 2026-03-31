from __future__ import annotations

import os
from typing import Any

import boto3
from botocore.config import Config

from ..core.config import get_db_config

_s3_client = None


def _get_client():
    global _s3_client
    if _s3_client is not None:
        return _s3_client

    cfg = get_db_config("object_storage")
    provider = cfg.get("provider", "minio")

    boto_kwargs: dict[str, Any] = {
        "aws_access_key_id": os.environ.get("MINIO_ACCESS_KEY") or os.environ.get("AWS_ACCESS_KEY_ID", ""),
        "aws_secret_access_key": os.environ.get("MINIO_SECRET_KEY") or os.environ.get("AWS_SECRET_ACCESS_KEY", ""),
        "config": Config(signature_version="s3v4"),
    }

    if provider == "minio":
        boto_kwargs["endpoint_url"] = cfg.get("endpoint", "http://minio:9000")
        boto_kwargs["region_name"] = "us-east-1"
    else:
        region = cfg.get("region", os.environ.get("AWS_REGION", "us-east-1"))
        boto_kwargs["region_name"] = region

    _s3_client = boto3.client("s3", **boto_kwargs)
    return _s3_client


def _get_bucket() -> str:
    cfg = get_db_config("object_storage")
    return cfg.get("bucket", "ascended")


async def file_upload(
    object_key: str,
    data: bytes,
    content_type: str = "application/octet-stream",
    metadata: dict | None = None,
) -> dict[str, Any]:
    client = _get_client()
    bucket = _get_bucket()
    extra_args: dict[str, Any] = {"ContentType": content_type}
    if metadata:
        extra_args["Metadata"] = {str(k): str(v) for k, v in metadata.items()}

    client.put_object(
        Bucket=bucket,
        Key=object_key,
        Body=data,
        **extra_args,
    )
    return {"bucket": bucket, "key": object_key, "size": len(data)}


async def file_retrieve(object_key: str) -> bytes:
    client = _get_client()
    bucket = _get_bucket()
    response = client.get_object(Bucket=bucket, Key=object_key)
    return response["Body"].read()


async def file_delete(object_key: str) -> None:
    client = _get_client()
    bucket = _get_bucket()
    client.delete_object(Bucket=bucket, Key=object_key)


async def presigned_url(
    object_key: str,
    expiration: int = 3600,
    operation: str = "get_object",
) -> str:
    client = _get_client()
    bucket = _get_bucket()
    url = client.generate_presigned_url(
        operation,
        Params={"Bucket": bucket, "Key": object_key},
        ExpiresIn=expiration,
    )
    return url


async def list_objects(prefix: str = "", max_keys: int = 100) -> list[dict[str, Any]]:
    client = _get_client()
    bucket = _get_bucket()
    response = client.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=max_keys)
    return [
        {"key": obj["Key"], "size": obj["Size"], "last_modified": str(obj["LastModified"])}
        for obj in response.get("Contents", [])
    ]
