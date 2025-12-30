import io
import logging
import re
from pathlib import Path
from typing import BinaryIO, Dict, List, Optional, Union, Any

import pandas as pd
from pypdf import PdfReader

try:
    import pdfplumber

    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    logging.warning("pdfplumber not available. Table extraction will be limited.")

logger = logging.getLogger(__name__)


PdfSource = Union[str, Path, BinaryIO, bytes, bytearray]


class PDFLoader:
    """PDF content extractor shared by RAG/earnings features."""

    @staticmethod
    def _open_reader(source: PdfSource) -> PdfReader:
        """Normalize source into PdfReader."""
        if source is None:
            raise ValueError("No PDF source provided")

        # Streamlit's UploadedFile behaves like a BinaryIO
        if hasattr(source, "read"):
            try:
                source.seek(0)
            except Exception:
                pass
            return PdfReader(source)

        if isinstance(source, (bytes, bytearray)):
            return PdfReader(io.BytesIO(source))

        return PdfReader(str(source))

    @classmethod
    def extract_text(
        cls,
        source: PdfSource,
        max_pages: Optional[int] = None,
        return_error_message: bool = False,
    ) -> str:
        """
        Extract text from any supported PDF source.

        Args:
            source: Path, bytes, or file-like object.
            max_pages: Optional max pages to read (useful for quick previews).
            return_error_message: If True, returns a user-facing error string instead of blank on failure.
        """
        if not source:
            return ""

        try:
            reader = cls._open_reader(source)
            text_parts: List[str] = []

            for idx, page in enumerate(reader.pages):
                if max_pages is not None and idx >= max_pages:
                    break
                page_text = page.extract_text() or ""
                page_text = page_text.strip()
                if page_text:
                    text_parts.append(page_text)

            return "\n\n".join(text_parts).strip()
        except Exception as e:
            logger.error(f"Error extracting PDF: {e}")
            if return_error_message:
                return f"Error extracting PDF: {str(e)}"
            return ""

    @classmethod
    def extract_text_from_file(cls, uploaded_file) -> str:
        """Extract text from a Streamlit UploadedFile object."""
        return cls.extract_text(uploaded_file, return_error_message=True)

    @classmethod
    def extract_text_from_path(cls, file_path: Union[str, Path]) -> str:
        """Extract text from a local file path."""
        return cls.extract_text(file_path, return_error_message=True)

    @classmethod
    def extract_tables(
        cls, source: PdfSource, max_pages: Optional[int] = None
    ) -> List[pd.DataFrame]:
        """
        Extract tables from PDF using pdfplumber

        Args:
            source: PDF source
            max_pages: Maximum pages to process

        Returns:
            List of DataFrames
        """
        if not PDFPLUMBER_AVAILABLE:
            logger.warning("pdfplumber not available. Cannot extract tables.")
            return []

        tables = []

        try:
            # Convert source to file-like object if needed
            if isinstance(source, (str, Path)):
                pdf_file = open(source, "rb")
                should_close = True
            elif hasattr(source, "read"):
                try:
                    source.seek(0)
                except BaseException:
                    pass
                pdf_file = source
                should_close = False
            elif isinstance(source, (bytes, bytearray)):
                pdf_file = io.BytesIO(source)
                should_close = False
            else:
                return []

            with pdfplumber.open(pdf_file) as pdf:
                for idx, page in enumerate(pdf.pages):
                    if max_pages and idx >= max_pages:
                        break

                    page_tables = page.extract_tables()
                    for table in page_tables:
                        if table:
                            try:
                                df = pd.DataFrame(table[1:], columns=table[0])
                                tables.append(df)
                            except BaseException:
                                # Fallback: no header
                                df = pd.DataFrame(table)
                                tables.append(df)

            if should_close:
                pdf_file.close()

            logger.info(f"Extracted {len(tables)} tables from PDF")
            return tables

        except Exception as e:
            logger.error(f"Failed to extract tables: {e}")
            return []

    @classmethod
    def extract_metadata(cls, source: PdfSource, text: str = None) -> Dict[str, Any]:
        """
        Extract metadata from PDF

        Args:
            source: PDF source
            text: Extracted text (optional, for text-based metadata extraction)

        Returns:
            Metadata dictionary
        """
        metadata = {"company": "Unknown", "date": "Unknown", "title": "Unknown"}

        try:
            reader = cls._open_reader(source)

            # PDF metadata
            if reader.metadata:
                if reader.metadata.title:
                    metadata["title"] = reader.metadata.title
                if reader.metadata.creation_date:
                    try:
                        metadata["date"] = reader.metadata.creation_date.strftime(
                            "%Y-%m-%d"
                        )
                    except BaseException:
                        pass

            # Text-based extraction
            if text:
                # 企業名抽出（例: "株式会社〇〇"）
                company_match = re.search(
                    r"(株式会社[^\s\n]+|[^\s\n]+株式会社)", text[:500]
                )
                if company_match:
                    metadata["company"] = company_match.group(1)

                # 日付抽出（例: "2024年11月1日"）
                date_match = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", text[:500])
                if date_match:
                    metadata[
                        "date"
                    ] = f"{date_match.group(1)}-{date_match.group(2):0>2}-{date_match.group(3):0>2}"

            return metadata

        except Exception as e:
            logger.error(f"Failed to extract metadata: {e}")
            return metadata

    @classmethod
    def load_pdf(cls, source: PdfSource, extract_tables: bool = True) -> Dict[str, Any]:
        """
        Load PDF with full extraction (text, tables, metadata)

        Args:
            source: PDF source
            extract_tables: Whether to extract tables

        Returns:
            Dictionary with text, tables, and metadata
        """
        try:
            # Extract text
            text = cls.extract_text(source)

            # Extract tables
            tables = []
            if extract_tables:
                tables = cls.extract_tables(source)

            # Extract metadata
            metadata = cls.extract_metadata(source, text)

            return {"text": text, "tables": tables, "metadata": metadata}

        except Exception as e:
            logger.error(f"Failed to load PDF: {e}")
            return {"text": "", "tables": [], "metadata": {}, "error": str(e)}

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 200) -> List[str]:
        """Split long text into slightly overlapping chunks for RAG/LLM prompts."""
        if not text:
            return []

        if chunk_size <= overlap:
            raise ValueError("chunk_size must be greater than overlap")

        cleaned = text.replace("\r\n", "\n").strip()
        chunks: List[str] = []
        start = 0

        # Guard against runaway loops in case of bad parameters
        max_iters = max(1, (len(cleaned) // max(chunk_size - overlap, 1)) + 2)
        for _ in range(max_iters):
            if start >= len(cleaned):
                break
            end = min(len(cleaned), start + chunk_size)
            chunk = cleaned[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start = end - overlap
        return chunks
