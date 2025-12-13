import io
from typing import List, Optional

from pypdf import PdfReader


class PDFLoader:
    """PDF content extractor for RAG"""

    @staticmethod
    def extract_text_from_file(uploaded_file) -> str:
        """Extract text from a Streamlit UploadedFile object"""
        if not uploaded_file:
            return ""

        try:
            # Read PDF from bytes
            reader = PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            return f"Error extracting PDF: {str(e)}"

    @staticmethod
    def extract_text_from_path(file_path: str) -> str:
        """Extract text from a local file path"""
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            return f"Error extracting PDF: {str(e)}"
