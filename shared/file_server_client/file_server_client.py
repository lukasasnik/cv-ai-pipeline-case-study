import json
import httpx
from .file_server_error import FileServerError
from .not_found_error import NotFoundError
from .file_upload_response import FileUploadResponse

class FileServerClient:
    """Client for interacting with the CV Pipeline File Server."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    async def upload(self, filename: str, content: bytes, content_type: str) -> FileUploadResponse:
        """
        Uploads a file to the file server.
        
        Returns:
            FileUploadResponse containing file metadata.
        Raises:
            FileServerError if the upload fails.
        """
        async with httpx.AsyncClient() as client:
            files = {"file": (filename, content, content_type)}
            try:
                response = await client.post(f"{self.base_url}/files/upload", files=files)
                response.raise_for_status()
                data = response.json()
                return FileUploadResponse(
                    id=data["id"],
                    filename=data["filename"],
                    size=data["size"],
                    created=data["created"]
                )
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise NotFoundError(f"File server endpoint not found: {e}")
                raise FileServerError(f"File server returned error {e.response.status_code}: {e.response.text}")
            except httpx.RequestError as e:
                raise FileServerError(f"Connection error to file server: {e}")

    async def upload_json(self, filename: str, data: dict | list) -> FileUploadResponse:
        """
        Serializes a dictionary or list to JSON and uploads it to the file server.
        
        Returns:
            FileUploadResponse containing file metadata.
        Raises:
            FileServerError if the upload fails.
        """
        try:
            content = json.dumps(data, indent=2).encode("utf-8")
            return await self.upload(filename, content, "application/json")
        except (TypeError, ValueError) as e:
            raise FileServerError(f"Failed to serialize data to JSON: {e}")

    async def download(self, file_id: str) -> bytes:
        """
        Downloads a file from the file server.
        
        Returns:
            The file content as bytes.
        Raises:
            NotFoundError if the file doesn't exist.
            FileServerError if the download fails.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/files/{file_id}")
                response.raise_for_status()
                return response.content
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise NotFoundError(f"File {file_id} not found on server")
                raise FileServerError(f"File server returned error {e.response.status_code}: {e.response.text}")
            except httpx.RequestError as e:
                raise FileServerError(f"Connection error to file server: {e}")

    async def download_text(self, file_id: str, encoding: str = "utf-8") -> str:
        """
        Downloads a file and decodes it as text.
        
        Returns:
            The file content as a string.
        Raises:
            NotFoundError if the file doesn't exist.
            FileServerError if the download or decoding fails.
        """
        content = await self.download(file_id)
        try:
            return content.decode(encoding)
        except UnicodeDecodeError as e:
            raise FileServerError(f"Failed to decode file {file_id} as {encoding}: {e}")

    async def delete(self, file_id: str) -> None:
        """
        Deletes a file from the file server.
        
        Raises:
            NotFoundError if the file doesn't exist.
            FileServerError if the deletion fails.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.delete(f"{self.base_url}/files/{file_id}")
                if response.status_code not in (200, 204, 404):
                    response.raise_for_status()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    # Depending on policy, we might ignore 404 on delete, 
                    # but following the request to encapsulate 404 in NotFoundError.
                    raise NotFoundError(f"File {file_id} not found for deletion")
                raise FileServerError(f"File server returned error {e.response.status_code}: {e.response.text}")
            except httpx.RequestError as e:
                raise FileServerError(f"Connection error to file server: {e}")
