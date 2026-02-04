import asyncio
from app.shared.storage.s3.objects import storage_s3_retrieve_objects_url
from app.shared.storage.utils import download_file_base64
from typing import List, Union


class DownloadStorageObjecs:
    async def download_by_path(
        self,
        relative_paths: Union[str, List[str]]
    ) -> List[str]:
        """
            Downloads one or more files from S3 storage using their relative paths.

            The function retrieves a temporary access URL for each provided path and
            downloads the corresponding file content encoded in Base64. Downloads are
            performed asynchronously with a concurrency limit to avoid resource
            exhaustion. If an error occurs while processing a path, `None` is returned
            for that specific item.

            Args:
                relative_paths (str | List[str]):
                    A single relative path or a list of relative paths pointing to
                    objects stored in S3.

            Returns:
                List[str]:
                    A list containing the Base64-encoded content of the downloaded
                    files. If a download fails, the corresponding list entry will be
                    None.
        """

        semaphore = asyncio.Semaphore(20)

        async def resolve(path: str):
            async with semaphore:
                try:
                    url = await storage_s3_retrieve_objects_url(path)
                    return await download_file_base64(url)
                except Exception:
                    return None

        if isinstance(relative_paths, list):
            result = await asyncio.gather(
                *[resolve(relative_path) for relative_path in relative_paths]
            )
            return result

        result = await asyncio.gather(
            resolve(relative_paths)
        )
        return result[0]
