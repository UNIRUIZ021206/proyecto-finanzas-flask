import os
from dotenv import load_dotenv
import sys

load_dotenv()

print(f"Python executable: {sys.executable}")

try:
    import google.generativeai as genai
    print("google.generativeai is installed.")
except ImportError:
    print("google.generativeai is NOT installed.")

api_key = os.getenv('GEMINI_API_KEY')
if api_key:
    print("GEMINI_API_KEY is found in environment.")
    # Check if it looks like a valid key (not empty)
    if len(api_key) > 10:
        print("GEMINI_API_KEY seems to have a valid length.")
    else:
        print("GEMINI_API_KEY is too short.")
else:
    print("GEMINI_API_KEY is NOT found in environment.")
