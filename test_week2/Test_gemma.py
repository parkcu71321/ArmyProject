import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemma-3-4b-it")
response = model.generate_content("Hello from Gemma 3 4B!")
print(response.text)

