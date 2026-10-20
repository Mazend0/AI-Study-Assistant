
import os
import json
import time
import uuid
from pathlib import Path
import tempfile
import streamlit as st
from dotenv import load_dotenv
from google import genai


# -------------------------
# 1. Configuration
# -------------------------

# -------------------------
# Modern dark UI styling
# -------------------------

st.markdown("""
<style>
/* Main application background */
.stApp {
    background: linear-gradient(
        135deg,
        #0e1117 0%,
        #111522 55%,
        #151126 100%
    );
}

/* Main content spacing */
.block-container {
    max-width: 1050px;
    padding-top: 2.5rem;
    padding-bottom: 3rem;
}

/* Main title */
h1 {
    color: #f1f5f9 !important;
    font-weight: 750 !important;
    letter-spacing: -1px;
}

/* Secondary headings */
h2, h3 {
    color: #e2e8f0 !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #11141d;
    border-right: 1px solid #262b3a;
}

/* Sidebar text */
section[data-testid="stSidebar"] p {
    color: #cbd5e1;
}

/* Buttons */
.stButton > button {
    border-radius: 12px;
    border: 1px solid #30364a;
    background: #191e2c;
    color: #f1f5f9;
    transition: all 0.2s ease;
}

/* Button hover */
.stButton > button:hover {
    border-color: #8b5cf6;
    color: #c4b5fd;
    background: #211b35;
}

/* Chat messages */
[data-testid="stChatMessage"] {
    background: rgba(25, 30, 44, 0.78);
    border: 1px solid #292f40;
    border-radius: 18px;
    padding: 1rem 1.2rem;
    margin-bottom: 1rem;
}

/* Chat input area */
[data-testid="stChatInput"] {
    border-radius: 18px;
}

/* Input focus */
[data-testid="stChatInput"] textarea:focus {
    border-color: #8b5cf6;
}

/* Dividers */
hr {
    border-color: #292f40;
}

/* Informational messages */
[data-testid="stAlert"] {
    border-radius: 14px;
}

/* Scrollbar */
::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-track {
    background: #0e1117;
}

::-webkit-scrollbar-thumb {
    background: #34384b;
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: #8b5cf6;
}
</style>
""", unsafe_allow_html=True)

load_dotenv()

CHAT_HISTORY_FILE = Path(__file__).parent / "chat_history.json"

st.set_page_config(
    page_title="AI Study Assistant",
    page_icon="📚",
    layout="wide",
)

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


# -------------------------
# 2. Chat functions
# -------------------------

def create_chat():
    return {
        "id": str(uuid.uuid4()),
        "title": "محادثة جديدة",
        "messages": [],
    }


def load_chat_data():
    if not CHAT_HISTORY_FILE.exists():
        return {"chats": [], "active_chat_id": None}

    try:
        with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        # Load the new storage format.
        if isinstance(data.get("chats"), list):
            return data

        # Old message history is intentionally not migrated.
        return {"chats": [], "active_chat_id": None}

    except (json.JSONDecodeError, OSError):
        return {"chats": [], "active_chat_id": None}


def save_chat_data():
    data = {
        "chats": st.session_state.chats,
        "active_chat_id": st.session_state.active_chat_id,
    }

    with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def get_active_chat():
    for chat in st.session_state.chats:
        if chat["id"] == st.session_state.active_chat_id:
            return chat

    return None


def new_chat():
    chat = create_chat()
    st.session_state.chats.insert(0, chat)
    st.session_state.active_chat_id = chat["id"]
    save_chat_data()


# -------------------------
# 3. Initialize session
# -------------------------

if "chats" not in st.session_state:
    saved_data = load_chat_data()

    st.session_state.chats = saved_data["chats"]
    st.session_state.active_chat_id = saved_data.get(
        "active_chat_id"
    )

    if not st.session_state.chats:
        chat = create_chat()
        st.session_state.chats = [chat]
        st.session_state.active_chat_id = chat["id"]

    elif not any(
        chat["id"] == st.session_state.active_chat_id
        for chat in st.session_state.chats
    ):
        st.session_state.active_chat_id = (
            st.session_state.chats[0]["id"]
        )

    save_chat_data()


# -------------------------
# 4. Gemini connection
# -------------------------

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("API key not found. Check your .env file.")
    st.stop()

client = genai.Client(api_key=api_key)


# -------------------------
# 5. Sidebar
# -------------------------

with st.sidebar:
    st.title("📚 Study Assistant")
    st.caption("مساعدك الدراسي الشخصي")

    if st.button(
        "➕ محادثة جديدة",
        use_container_width=True,
        type="primary",
    ):
        new_chat()
        st.rerun()

    st.divider()
    st.subheader("محادثاتك السابقة")

    if not st.session_state.chats:
        st.caption("لا توجد محادثات بعد.")

    for chat in st.session_state.chats:
        col_chat, col_delete = st.columns([5, 1])

        with col_chat:
            title = chat["title"]

            if len(title) > 25:
                title = title[:25] + "..."

            if st.button(
                title,
                key=f"open_{chat['id']}",
                use_container_width=True,
                type=(
                    "primary"
                    if chat["id"] == st.session_state.active_chat_id
                    else "secondary"
                ),
            ):
                st.session_state.active_chat_id = chat["id"]
                save_chat_data()
                st.rerun()

        with col_delete:
            if st.button(
                "🗑️",
                key=f"delete_{chat['id']}",
                help="حذف هذه المحادثة",
                use_container_width=True,
            ):
                st.session_state.chats = [
                    item
                    for item in st.session_state.chats
                    if item["id"] != chat["id"]
                ]

                if (
                    st.session_state.active_chat_id
                    == chat["id"]
                ):
                    if st.session_state.chats:
                        st.session_state.active_chat_id = (
                            st.session_state.chats[0]["id"]
                        )
                    else:
                        replacement = create_chat()
                        st.session_state.chats = [replacement]
                        st.session_state.active_chat_id = (
                            replacement["id"]
                        )

                save_chat_data()
                st.rerun()


# -------------------------
# 6. Display active chat
# -------------------------

active_chat = get_active_chat()

if active_chat is None:
    new_chat()
    st.rerun()

st.title("📚 AI Study Assistant")
st.caption("Your personal study assistant")


if not active_chat["messages"]:
    st.markdown(
        """
        <div style="text-align:center; padding: 35px 0 20px 0;">
            <div style="font-size:52px;">📚</div>
            <h2 style="margin-bottom:8px;">
                مرحبًا بك في مساعدك الدراسي
            </h2>
            <p style="color:#A9B2C5;">
                تعلّم، استكشف، وطوّر مهاراتك خطوة بخطوة.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("### 🚀 وش ودك تتعلم اليوم؟")

    col1, col2 = st.columns(2)

    with col1:
        explain_clicked = st.button(
            "💻 تعلم البرمجة",
            use_container_width=True,
        )
        summarize_clicked = st.button(
            "📝 لخّص لي درسًا",
            use_container_width=True,
        )

    with col2:
        quiz_clicked = st.button(
            "🧠 اختبر معلوماتي",
            use_container_width=True,
        )
        concept_clicked = st.button(
            "💡 اشرح لي مفهومًا",
            use_container_width=True,
        )

    if explain_clicked:
        st.session_state.starter_prompt = (
            "علّمني مفهومًا في Python مع أمثلة عملية "
            "وتدريب قصير."
        )
        st.rerun()

    if summarize_clicked:
        st.session_state.starter_prompt = (
            "ساعدني في تلخيص درس. اطلب مني إرسال نص الدرس أولًا."
        )
        st.rerun()

    if quiz_clicked:
        st.session_state.starter_prompt = (
            "اختبر معلوماتي في البرمجة بعشرة أسئلة، "
            "سؤالًا واحدًا في كل مرة."
        )
        st.rerun()

    if concept_clicked:
        st.session_state.starter_prompt = (
            "اقترح مفهومًا مهمًا في علوم الحاسب "
            "واشرحه لي بطريقة بسيطة."
        )
        st.rerun()


for message in active_chat["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# -------------------------
# 7. Chat with Gemini
# -------------------------

# -------------------------
# PDF summary and interactive quiz
# -------------------------
with st.expander("📄 رفع ملف PDF وتلخيصه أو اختبر نفسك", expanded=False):
    uploaded_pdf = st.file_uploader(
        "اختر ملف محاضرة أو كتاب",
        type=["pdf"],
        key="pdf_uploader",
    )
    num_questions = st.selectbox(
        "عدد أسئلة الاختبار",
        [5, 10, 15],
        index=0,
    )
    col_summary, col_quiz = st.columns(2)

    with col_summary:
        summarize_clicked = st.button(
            "✨ تلخيص الملف",
            disabled=uploaded_pdf is None,
            use_container_width=True,
        )

    with col_quiz:
        quiz_clicked = st.button(
            "🧠 إنشاء اختبار",
            disabled=uploaded_pdf is None,
            use_container_width=True,
        )

    if summarize_clicked or quiz_clicked:
        temp_path = None

        try:
            with st.spinner(
                "جاري إعداد المحتوى..." if quiz_clicked
                else "جاري قراءة الملف وتلخيصه..."
            ):
                with tempfile.NamedTemporaryFile(
                    suffix=".pdf",
                    delete=False,
                ) as temp_file:
                    temp_file.write(uploaded_pdf.getvalue())
                    temp_path = temp_file.name

                try:
                    pdf_file = client.files.upload(file=temp_path)

                    if summarize_clicked:
                        response = client.models.generate_content(
                            model="gemini-3.8-flash",
                            contents=[
                                pdf_file,
                                """
                                لخّص الملف باللغة العربية للطالب.
                                اذكر الفكرة العامة، وأهم المفاهيم،
                                والتعريفات والأمثلة المهمة.
                                التزم بمحتوى الملف.
                                """,
                            ],
                        )

                        summary = response.text or "لم يصلني تلخيص نصي."

                        active_chat["messages"].append({
                            "role": "user",
                            "content": f"📄 تلخيص الملف: {uploaded_pdf.name}",
                        })
                        active_chat["messages"].append({
                            "role": "assistant",
                            "content": summary,
                        })

                        if active_chat["title"] == "محادثة جديدة":
                            active_chat["title"] = (
                                f"تلخيص: {uploaded_pdf.name}"[:35]
                            )

                        save_chat_data()
                        st.success("تم التلخيص وحفظه في المحادثة!")

                    else:
                        response = client.models.generate_content(
                            model="gemini-3.8-flash",
                            contents=[
                                pdf_file,
                                """
                                أنشئ اختبارًا من محتوى ملف PDF.
                                أخرج JSON صالحًا فقط، دون Markdown،
                                وبالشكل التالي:
                                {
                                  "questions": [
                                    {
                                      "question": "نص السؤال",
                                      "options": [
                                        "الخيار الأول",
                                        "الخيار الثاني",
                                        "الخيار الثالث",
                                        "الخيار الرابع"
                                      ],
                                      "answer": 0,
                                      "explanation": "شرح الإجابة"
                                    }
                                  ]
                                }

                               عدد الأسئلة المطلوب: __COUNT__ باللغة العربية.
                                يجب أن تكون answer رقمًا من 0 إلى 3
                                يشير إلى الخيار الصحيح.
                                اجعل الأسئلة مبنية على الملف فقط.
                                """.replace("__COUNT__", str(num_questions)),
                            ],
                        )

                        raw_text = response.text or ""
                        raw_text = raw_text.strip()

                        if raw_text.startswith("```"):
                            raw_text = raw_text.split("\n", 1)[1]
                            raw_text = raw_text.rsplit("```", 1)[0].strip()

                        quiz_data = json.loads(raw_text)
                        questions = quiz_data.get("questions", [])

                        if not questions:
                            st.error("لم يتم العثور على أسئلة في النتيجة.")
                        else:
                            valid_questions = [
                                q for q in questions
                                if isinstance(q, dict)
                                and isinstance(q.get("question"), str)
                                and isinstance(q.get("options"), list)
                                and len(q["options"]) == 4
                                and isinstance(q.get("answer"), int)
                                and 0 <= q["answer"] < 4
                            ]

                            if not valid_questions:
                                st.error(
                                    "وصلت أسئلة بصيغة غير متوقعة. "
                                    "جرّب إنشاء الاختبار مرة أخرى."
                                )
                            else:
                                st.session_state.quiz_questions = valid_questions
                                st.session_state.quiz_index = 0
                                st.session_state.quiz_score = 0
                                st.session_state.quiz_answered = False
                                st.session_state.quiz_feedback = None
                                st.session_state.quiz_selections = {}
                                st.session_state.quiz_filename = uploaded_pdf.name

                                st.success("تم إنشاء الاختبار!")
                                st.rerun()

                finally:
                    if temp_path and os.path.exists(temp_path):
                        os.remove(temp_path)

        except json.JSONDecodeError:
            st.error(
                "تعذر قراءة الأسئلة التي أنشأها Gemini. "
                "حاول إنشاء الاختبار مرة أخرى."
            )
        except Exception as e:
            st.error(f"حدث خطأ أثناء معالجة الملف: {e}")


# -------------------------
# Interactive quiz
# -------------------------

if st.session_state.get("quiz_questions"):
    questions = st.session_state.quiz_questions
    index = st.session_state.quiz_index

    st.divider()
    st.subheader("🧠 اختبارك الدراسي")
    st.caption(f"الملف: {st.session_state.quiz_filename}")

    if index < len(questions):
        question = questions[index]

        st.progress((index + 1) / len(questions))
        st.write(f"**السؤال {index + 1} من {len(questions)}**")
        st.markdown(f"### {question['question']}")

        selection_key = f"quiz_selection_{index}"

        selected = st.radio(
            "اختر الإجابة الصحيحة:",
            options=range(4),
            format_func=lambda i: question["options"][i],
            key=selection_key,
            disabled=st.session_state.quiz_answered,
        )

        if not st.session_state.quiz_answered:
            if st.button("تحقق من الإجابة", type="primary"):
                correct = selected == question["answer"]

                if correct:
                    st.session_state.quiz_score += 1

                st.session_state.quiz_answered = True
                st.session_state.quiz_feedback = {
                    "correct": correct,
                    "answer": question["answer"],
                    "explanation": question.get(
                        "explanation", ""
                    ),
                }
                st.rerun()

        if st.session_state.quiz_answered:
            feedback = st.session_state.quiz_feedback

            if feedback["correct"]:
                st.success("إجابة صحيحة! 🎉")
            else:
                st.error(
                    "إجابة غير صحيحة. الإجابة الصحيحة: "
                    + question["options"][feedback["answer"]]
                )

            if feedback["explanation"]:
                st.info(feedback["explanation"])

            if st.button(
                "السؤال التالي ➜"
                if index + 1 < len(questions)
                else "عرض النتيجة 🏆",
                type="primary",
            ):
                st.session_state.quiz_index += 1
                st.session_state.quiz_answered = False
                st.session_state.quiz_feedback = None
                st.rerun()

    else:
        score = st.session_state.quiz_score
        total = len(questions)

        st.success(f"انتهى الاختبار! نتيجتك: {score} من {total}")
        st.metric("نسبة الإجابات الصحيحة", f"{score / total * 100:.0f}%")

        if st.button("إعادة الاختبار"):
            st.session_state.quiz_index = 0
            st.session_state.quiz_score = 0
            st.session_state.quiz_answered = False
            st.session_state.quiz_feedback = None
            st.rerun()
# Keep the chat input outside the PDF expander
prompt = st.chat_input("اكتب سؤالك هنا...")

if prompt:
    active_chat["messages"].append(
        {"role": "user", "content": prompt}
    )

    # Use the first question as the chat title.
    if active_chat["title"] == "محادثة جديدة":
        active_chat["title"] = prompt.strip()[:35]

    save_chat_data()

    with st.chat_message("user"):
        st.markdown(prompt)


    with st.chat_message("assistant"):
        with st.spinner("جاري التفكير..."):
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
                                    "user"
                                    if message["role"] == "user"
                                    else "model"
                                ),
                                "parts": [
                                    {"text": message["content"]}
                                ],
                            }
                            for message in active_chat["messages"]
                        ],
                    )

                    reply = (
                        response.text or "لم يصلني رد نصي."
                    )

                    st.markdown(reply)

                    active_chat["messages"].append(
                        {
                            "role": "assistant",
                            "content": reply,
                        }
                    )

                    save_chat_data()
                    break

                except Exception as e:
                    error = str(e)

                    if "503" in error and attempt < 2:
                        time.sleep(2 * (attempt + 1))
                        continue

                    if "503" in error:
                        st.error(
                            "خدمة Gemini مشغولة حاليًا. "
                            "حاول مرة أخرى بعد قليل."
                        )
                    elif "429" in error:
                        st.error(
                            "وصلت إلى حد الاستخدام المتاح حاليًا. "
                            "تحقق من حصة Gemini وحاول لاحقًا."
                        )
                    else:
                        st.error(
                            f"حدث خطأ أثناء الاتصال: {error}"
                        )

                    break

                 # python -m streamlit run app.py <<<<هذا كود تشغيل الموقع 
  
                 

                 
