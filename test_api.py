import google.generativeai as genai
import inspect

print(f"genai module path: {genai.__file__}")
genai.configure(api_key='AIzaSyAexlNkrA7VtvKa5FqfVo30m6bHoPgveIg')
try:
    print("\n--- AVAILABLE MODELS ---")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Model ID: {m.name}")
except Exception as e:
    print(f"Error fetching models: {e}")
