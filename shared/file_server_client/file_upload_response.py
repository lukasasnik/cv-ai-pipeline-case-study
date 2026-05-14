from dataclasses import dataclass

@dataclass
class FileUploadResponse:
    """Metadata returned after a successful file upload."""
    id: str
    filename: str
    size: int
    created: bool
