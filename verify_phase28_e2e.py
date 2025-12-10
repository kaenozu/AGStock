
import os
from reportlab.pdfgen import canvas
from src.analysis.pdf_reader import PDFExtractor

def create_dummy_pdf(filename: str):
    """Creates a simple PDF with known text."""
    c = canvas.Canvas(filename)
    c.drawString(100, 750, "AGStock Corporation Financial Report")
    c.drawString(100, 730, "Period: 2024 Q1")
    c.drawString(100, 710, "Summary: Revenue increased by 20% year-over-year.")
    c.drawString(100, 690, "Positive: Strong growth in AI sector.")
    c.drawString(100, 670, "Negative: Rising server costs.")
    c.save()

def test_pdf_extraction_e2e():
    print("\n[VERIFY] Phase 28: End-to-End PDF Extraction")
    
    filename = "test_earnings.pdf"
    
    # 1. Generate PDF
    try:
        print(f"  Generating {filename}...")
        create_dummy_pdf(filename)
    except Exception as e:
        print(f"  FAILURE: Could not generate PDF (reportlab error?): {e}")
        return

    # 2. Extract Text
    try:
        print("  Extracting text...")
        # PDFExtractor expects a file-like object or path. pypdf handles paths string too.
        # But st.file_uploader returns a stream. Let's open it as rb to simulate.
        with open(filename, "rb") as f:
            text = PDFExtractor.extract_text(f)
        
        print(f"  Extracted {len(text)} characters.")
        
        # 3. Verify Content
        expected_keywords = ["AGStock", "Revenue increased", "AI sector"]
        missing = [k for k in expected_keywords if k not in text]
        
        if not missing:
            print("  Content Verification: SUCCESS")
            print(f"  Sample: {text[:50]}...")
        else:
            print(f"  FAILURE: Missing keywords: {missing}")
            print(f"  Full Text: {text}")
            
    except Exception as e:
        print(f"  FAILURE: Extraction failed: {e}")
    finally:
        # Cleanup
        if os.path.exists(filename):
            os.remove(filename)

if __name__ == "__main__":
    test_pdf_extraction_e2e()
