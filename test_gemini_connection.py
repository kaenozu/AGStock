import google.generativeai as genai
import os
import json

def test_connection():
    print("Reading config...")
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
            api_key = config.get("gemini_api_key")
    except Exception as e:
        print(f"Config error: {e}")
        return

    if not api_key:
        print("No API Key found.")
        return

    genai.configure(api_key=api_key)
    model_name = "gemini-2.0-flash" 
    
    print(f"Testing model: {model_name}...")
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Hello, can you hear me?")
        print(f"Response: {response.text}")
        print("SUCCESS: Connection verified.")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_connection()
