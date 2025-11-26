import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

print(f"API Key found: {'Yes' if GEMINI_API_KEY else 'No'}")

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash-lite')
        print("Model initialized. Generating content...")
        response = model.generate_content("Say 'Hello, World!'")
        print("Response received:")
        print(response.text)
    except Exception as e:
        print(f"Error: {e}")
else:
    print("Skipping test because API key is missing.")
