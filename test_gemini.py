import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("لم يتم العثور على مفتاح API في ملف .env")
else:
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents="عرّف بنفسك في جملة واحدة باللغة العربية."
    )

    print(response.text)
