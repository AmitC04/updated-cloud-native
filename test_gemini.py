import google.generativeai as genai
import os

genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))
try:
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content("Hello, what models are available?")
    print("Success with gemini-pro!")
    print(response.text[:200])
except Exception as e:
    print(f"Error with gemini-pro: {e}")
    
    try:
        model = genai.GenerativeModel('models/gemini-pro')
        response = model.generate_content("Hello!")
        print("Success with models/gemini-pro!")
        print(response.text[:200])
    except Exception as e2:
        print(f"Error with models/gemini-pro: {e2}")