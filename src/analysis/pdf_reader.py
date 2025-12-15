import logging
from typing import Dict

from src.rag.pdf_loader import PDFLoader
from src.llm_reasoner import get_llm_reasoner

logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extracts text from PDF files."""

    @staticmethod
    def extract_text(file_stream) -> str:
        """
        Extracts text from a PDF file stream.

        Args:
            file_stream: The uploaded file stream (e.g. from st.file_uploader)

        Returns:
            Extracted text content as string.
        """
        text = PDFLoader.extract_text(file_stream, return_error_message=True)
        if not text:
            logger.error("PDF extraction returned no text. The PDF may be image-based or corrupted.")
        return text


class EarningsAnalyzer:
    """Analyzes earnings reports using LLM."""

    def __init__(self):
        self.llm = get_llm_reasoner()

    def analyze_report(self, text: str) -> Dict[str, str]:
        """
        Generates analysis from raw text using Gemini.
        Returns a dictionary with summary, sentiment, and details.
        """
        # Reuse the existing method in LLMReasoner which handles the prompt
        return self.llm.analyze_earnings_report(text)
