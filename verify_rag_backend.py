import os
import io
import json
from reportlab.pdfgen import canvas
from src.rag.pdf_loader import PDFLoader
from src.llm_reasoner import get_llm_reasoner

# 1. Create Dummy PDF
pdf_path = "mock_earnings.pdf"
print(f"Generating {pdf_path}...")

c = canvas.Canvas(pdf_path)
c.drawString(100, 800, "AGStock Corp FY2025 Earnings Report")
c.drawString(100, 780, "Summary:")
c.drawString(100, 760, "Revenue increased by 150% YoY driven by AI adoption.")
c.drawString(100, 740, "Operating Income reached record high of 5B JPY.")
c.drawString(100, 720, "However, R&D costs increased by 30% due to GPU investments.")
c.drawString(100, 700, "Outlook:")
c.drawString(100, 680, "We expect continued growth in Q4. Dividends will be raised by 10 JPY.")
c.save()

# 2. Extract Text
print("Extracting text...")
text = PDFLoader.extract_text_from_path(pdf_path)
print(f"Extracted: {text[:100]}...")

# 3. Analyze with LLM (OpenAI preferably)
print("Analyzing with LLM...")
reasoner = get_llm_reasoner()
if not reasoner.api_key:
    print("FATAL: No API Key found.")
else:
    # Force OpenAI if available logic is handled inside reasoner, but let's see.
    result = reasoner.analyze_earnings_report(text)
    print("Analysis Result:")
    print(json.dumps(result, indent=2, ensure_ascii=False))

# Cleanup
# os.remove(pdf_path)
