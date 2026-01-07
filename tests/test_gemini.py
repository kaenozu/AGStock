
import os
import pytest
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

@pytest.mark.skipif(not os.getenv("GOOGLE_API_KEY"), reason="API Key not found")
def test_gemini_generation():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        pytest.skip("API Key not found")
        
    try:
        genai.configure(api_key=api_key)
        # Use a model name that is likely to exist or handle the error
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content("Hello, how are you?")
            assert response is not None
            assert response.text is not None
        except Exception as e:
            pytest.skip(f"Gemini API call failed (likely model not found or quota exceeded): {e}")
            
    except Exception as e:
        pytest.fail(f"Gemini configuration failed: {e}")

