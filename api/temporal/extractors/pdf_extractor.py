import fitz  # PyMuPDF
from temporal.extractors.base_extractor import BaseExtractor

class PDFExtractor(BaseExtractor):
    """Extracts raw text from PDF documents using PyMuPDF."""

    def extract(self, file_bytes: bytes) -> str:
        """
        Extract raw text from PDF file bytes.

        Args:
            file_bytes: The raw bytes of the PDF.

        Returns:
            The extracted text as a string.

        Raises:
            ValueError: If the file cannot be parsed as a valid PDF.
        """
        try:
            # Open the document from memory
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            
            extracted_text = []
            for page in doc:
                # Extract text preserving blocks/paragraphs roughly
                text = page.get_text("text")
                if text:
                    extracted_text.append(text)
            
            doc.close()
            return "\n".join(extracted_text)
            
        except Exception as e:
            # Wrap PyMuPDF exceptions in ValueError for the caller
            raise ValueError(f"Failed to extract text from PDF: {e}") from e
