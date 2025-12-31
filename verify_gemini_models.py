import json
import os

import google.generativeai as genai


def list_models():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                api_key = config.get("gemini_api_key")
        except Exception:
            pass

    if not api_key:
        print("No API Key found.")
        return

    genai.configure(api_key=api_key)

    print("Listing available models...")
    try:
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
                print(f"- {m.name}")
    except Exception as e:
        print(f"Error listing models: {e}")


if __name__ == "__main__":
    list_models()
