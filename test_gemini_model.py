import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=api_key)

model_name = 'gemini-2.0-flash-lite'
print(f"Testing model: {model_name}")

try:
    model = genai.GenerativeModel(model_name)
    response = model.generate_content("Hello, are you working?")
    print("Response received:")
    print(response.text)
except Exception as e:
    print(f"Error with model {model_name}: {e}")
    
    # Try fallback
    fallback_model = 'gemini-1.5-flash'
    print(f"Testing fallback model: {fallback_model}")
    try:
        model = genai.GenerativeModel(fallback_model)
        response = model.generate_content("Hello, are you working?")
        print("Response received from fallback:")
        print(response.text)
    except Exception as e2:
        print(f"Error with fallback model {fallback_model}: {e2}")
