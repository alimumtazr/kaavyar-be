from minio import Minio
from minio.error import S3Error
from typing import Optional
import io
from .config import settings


class MinIOClient:
    client: Optional[Minio] = None


minio_client = MinIOClient()


def connect_to_minio():
    """Create MinIO connection and ensure bucket exists."""
    minio_client.client = Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE
    )
    
    # Ensure bucket exists
    try:
        if not minio_client.client.bucket_exists(settings.MINIO_BUCKET):
            minio_client.client.make_bucket(settings.MINIO_BUCKET)
            # Set bucket policy for public read access
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": "*"},
                        "Action": ["s3:GetObject"],
                        "Resource": [f"arn:aws:s3:::{settings.MINIO_BUCKET}/*"]
                    }
                ]
            }
            import json
            minio_client.client.set_bucket_policy(settings.MINIO_BUCKET, json.dumps(policy))
        print(f"Connected to MinIO, bucket: {settings.MINIO_BUCKET}")
    except S3Error as e:
        print(f"MinIO connection error: {e}")


async def upload_file(file_data: bytes, object_name: str, content_type: str) -> str:
    """Upload file to MinIO and return URL."""
    try:
        minio_client.client.put_object(
            settings.MINIO_BUCKET,
            object_name,
            io.BytesIO(file_data),
            length=len(file_data),
            content_type=content_type
        )
        
        # Return public URL
        protocol = "https" if settings.MINIO_SECURE else "http"
        return f"{protocol}://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET}/{object_name}"
    except S3Error as e:
        raise Exception(f"Failed to upload file: {e}")


async def delete_file(object_name: str) -> bool:
    """Delete file from MinIO."""
    try:
        minio_client.client.remove_object(settings.MINIO_BUCKET, object_name)
        return True
    except S3Error as e:
        print(f"Failed to delete file: {e}")
        return False


def get_minio_client() -> Minio:
    """Get MinIO client instance."""
    return minio_client.client







