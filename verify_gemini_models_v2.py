import json
import os

import google.generativeai as genai

print("Checking config.json...")
try:
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
        api_key = config.get("gemini_api_key")
        print(f"Key found: {api_key[:5]}...")
except Exception as e:
    print(f"Error reading config: {e}")
    api_key = None

if not api_key:
    print("FATAL: Key missing")
    exit()

genai.configure(api_key=api_key)

print("Listing models...")
try:
    for m in genai.list_models():
        if "generateContent" in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"API Error: {e}")
