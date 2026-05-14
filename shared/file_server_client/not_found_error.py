from .file_server_error import FileServerError

class NotFoundError(FileServerError):
    """Exception raised when a file is not found on the file server."""
    pass
