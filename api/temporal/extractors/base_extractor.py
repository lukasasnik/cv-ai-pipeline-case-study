from abc import ABC, abstractmethod

class BaseExtractor(ABC):
    """Abstract base class for document text extractors."""

    @abstractmethod
    def extract(self, file_bytes: bytes) -> str:
        """
        Extract raw text from file bytes.

        Args:
            file_bytes: The raw bytes of the file to process.

        Returns:
            The extracted text as a string.

        Raises:
            ValueError: If the file cannot be parsed or is invalid.
        """
        pass
