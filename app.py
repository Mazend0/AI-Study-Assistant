import os
import streamlit as st
from dotenv import load_dotenv
from google import genai
import time
import json
from pathlib import Path

load_dotenv()
CHAT_HISTORY_FILE = Path(__file__).parent / "chat_history.json"


def load_chat_history():

    if not CHAT_HISTORY_FILE.exists():
        return []

    try:
        with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data.get("messages", [])
    except (json.JSONDecodeError, OSError):
        return []
def save_chat_history(messages):
    data = {"messages": messages}

    with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

st.set_page_config(
    page_title="AI Study Assistant",
    page_icon="📚"
)

st.title("📚 AI Study Assistant")
st.write("Your personal study assistant")

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("API key not found. Check your .env file.")
    st.stop()

client = genai.Client(api_key=api_key)
SYSTEM_INSTRUCTION = """
أنت مساعد دراسي ذكي واسمك AI Study Assistant.

مهمتك:
1. شرح الدروس بطريقة بسيطة وواضحة.
2. تلخيص النصوص واستخراج أهم النقاط.
3. إنشاء أسئلة اختبارات مع الإجابات.
4. مساعدة الطالب على فهم البرمجة وحل المشكلات خطوة بخطوة.
5. إذا لم يفهم الطالب، اشرح له بطريقة أسهل مع أمثلة.
6. أجب بلغة المستخدم، واستخدم العربية إذا كتب بالعربية.
7. لا تعطِ إجابة مختصرة فقط عندما يحتاج الطالب إلى شرح مفصل.
"""

if "messages" not in st.session_state:
    st.session_state.messages = load_chat_history()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

prompt = st.chat_input("Ask me anything...")

if prompt:
    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    save_chat_history(st.session_state.messages)

    with st.chat_message("user"):
        st.write(prompt)

        with st.chat_message("assistant"):
         with st.spinner("Thinking..."):
            for attempt in range(3):
                try:
                    response = client.models.generate_content(
    model="gemini-3.8-flash",
    config={
        "system_instruction": SYSTEM_INSTRUCTION
    },
    contents=[
                            {
                                "role": (
                                    "user" if message["role"] == "user"
                                    else "model"
                                ),
                                "parts": [{"text": message["content"]}]
                            }
                            for message in st.session_state.messages
                        ]
                    )

                    reply = response.text or "لم يصلني رد نصي."
                    st.write(reply)

                    st.session_state.messages.append(
                        {"role": "assistant", "content": reply}
                    )
                    save_chat_history(st.session_state.messages)
                    break

                except Exception as e:
                    error = str(e)

                    if "503" in error and attempt < 2:
                        time.sleep(2 * (attempt + 1))
                        continue

                    if "503" in error:
                        st.error(
                            "خدمة Gemini مشغولة حاليًا. "
                            "انتظر قليلًا ثم حاول مجددًا."
                        )
                    else:
                        st.error(f"حدث خطأ أثناء الاتصال: {error}")

                    break
                except Exception as e:
                 st.error(f"Something went wrong: {e}")

                 
                 # python -m streamlit run app.py <<<<هذا كود تشغيل الموقع 
  
                 

                 