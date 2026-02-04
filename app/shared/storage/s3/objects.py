import os
from starlette.datastructures import UploadFile
from app.shared.exceptions.storage import StorageError
from app.shared.storage.s3.client import get_s3_client
from typing import Union, List
from uuid import uuid4
from pathlib import Path
from datetime import datetime
import asyncio
from app.shared.files.files_type_choices import FileTypeChoices
from pathlib import Path, PurePosixPath


def generate_s3_storage_object_key(prefix: str, file: UploadFile) -> str:
    if not isinstance(file, UploadFile):
        raise ValueError("File must be a UploadFile instance.")

    path = Path(file.filename)
    file_name = path.stem.lower().replace(" ", "_")
    extension = path.suffix.lower()
    timestamp = datetime.now().strftime("%d%m%Y_%H%M%S")

    return (
        f"{prefix}/"
        f"{file_name}__{timestamp}__{uuid4()}{extension}"
    )

def generate_s3_storage_move_object_key(
        full_source_path: str,
        relative_destination_path: str
    ) -> str:
        file_name = Path(full_source_path).name
        return str(PurePosixPath(relative_destination_path) / file_name)

def generate_s3_temporary_storage_object_key(extension: FileTypeChoices) -> str:
    prefix = os.getenv("AWS_S3_TEMPORARY_PREFIX_STORAGE")
    if not prefix:
        raise ValueError("AWS_S3_TEMPORARY_PREFIX_STORAGE not present in .env")

    timestamp = datetime.now().strftime("%d%m%Y_%H%M%S")
    return (
        f"{prefix}/"
        f"{timestamp}__{uuid4()}.{extension.value}"
    )

def generate_s3_presigned_url(key: str, expires_in: int = 3600) -> str:
    bucket_name = os.getenv("AWS_S3_BUCKET")
    if not bucket_name:
        raise ValueError("AWS_S3_BUCKET not present in .env")
    
    try:
        s3_client = get_s3_client()
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": key},
            ExpiresIn=expires_in
        )
    except Exception as error:
        raise StorageError(
            f"Error on generate presigned URL for {key}: {error}"
        )

    return url

def storage_s3_save_object(file: UploadFile, relative_save_path: str) -> str:
    bucket_name = os.getenv("AWS_S3_BUCKET")
    if not bucket_name:
        raise StorageError("AWS_S3_BUCKET not present in .env.")

    try:
        get_s3_client().upload_fileobj(
            file.file,
            bucket_name,
            relative_save_path
        )
    except Exception as error:
        raise StorageError(
            f"Error saving object to cloud storage: {error}."
        )

    return generate_s3_presigned_url(relative_save_path)

async def storage_s3_retrieve_objects_url(relative_paths: Union[str, List[str]]) -> Union[None, str, List[str]]:
    if not relative_paths:
        return None

    def generate_presigned_url(relative_path):
        return generate_s3_presigned_url(relative_path)

    if isinstance(relative_paths, list):
        try:
            async_loop = asyncio.get_running_loop()
            tasks = [async_loop.run_in_executor(None, generate_presigned_url, relative_path) for relative_path in relative_paths]
            results = await asyncio.gather(*tasks)
            return [result for result in results if result]        
        except Exception as error:
            raise StorageError(
                f"Error on retreave presigned object url, original error - {str(error)}."
            )

    return generate_presigned_url(relative_paths)

def storage_s3_save_object(file: UploadFile, relative_save_path: str) -> str:
    bucket_name = os.getenv("AWS_S3_BUCKET")
    if not bucket_name:
        raise StorageError("AWS_S3_BUCKET not present in .env.")

    try:
        get_s3_client().upload_fileobj(
            file.file,
            bucket_name,
            relative_save_path
        )
    except Exception as error:
        raise StorageError(
            f"Error saving object to cloud storage: {error}."
        )

    return generate_s3_presigned_url(relative_save_path)

def storage_s3_move_object(
    source_key: str,
    destination_key: str
) -> str:

    bucket_name = os.getenv("AWS_S3_BUCKET")
    if not bucket_name:
        raise StorageError("AWS_S3_BUCKET not present in .env.")
        
    s3_client = get_s3_client()

    try:
        s3_client.copy_object(
            Bucket=bucket_name,
            CopySource={
                "Bucket": bucket_name,
                "Key": source_key
            },
            Key=destination_key
        )

        s3_client.delete_object(
            Bucket=bucket_name,
            Key=source_key
        )

    except Exception as error:
        raise StorageError(
            f"Error moving object from {source_key} to {destination_key}: {error}"
        )

    return destination_key
