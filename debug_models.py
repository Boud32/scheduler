import os
from google import genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY not set.")
else:
    client = genai.Client(api_key=GEMINI_API_KEY)
    print("Listing available models...")
    try:
        for m in client.models.list():
            # The new SDK model object structure might be different, usually it has .name or .display_name
            # The old SDK filtered by supported_generation_methods, 
            # the new one lists all models but we can just print them.
            print(f"- {m.name}")
    except Exception as e:
        print(f"Error: {e}")
