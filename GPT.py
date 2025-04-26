import os
from dotenv import load_dotenv
import streamlit as st
from openai import OpenAI

# ── Load .env & API key ───────────────────────────────────────────────
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("🔑 OPENAI_API_KEY not found. Add it to a .env file.")
    st.stop()

client = OpenAI(api_key=OPENAI_API_KEY)

st.set_page_config(page_title="OpenAI Playground", layout="centered")

# ── Sidebar navigation ────────────────────────────────────────────────
page = st.sidebar.radio("Go to:", ["Chat", "Image"])
st.sidebar.markdown("---")
st.sidebar.markdown("Powered by OpenAI")

# ── Session-state defaults ────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "input_area" not in st.session_state:
    st.session_state.input_area = ""

# ── Chat page callback ────────────────────────────────────────────────
def generate_text():
    prompt = st.session_state.input_area.strip()
    if not prompt:
        st.warning("Please enter a prompt.")
        return

    # 1) record user message
    st.session_state.chat_history.append({"role": "user", "content": prompt})

    # 2) send to OpenAI
    try:
        resp = client.responses.create(
            model="gpt-4.1",
            input=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user",   "content": prompt},
            ],
        )
        reply = resp.output_text
    except Exception as e:
        st.error(f"API error: {e}")
        return

    # 3) record assistant reply
    st.session_state.chat_history.append({"role": "assistant", "content": reply})

    # 4) clear input box
    st.session_state.input_area = ""

# ── Render Chat page ──────────────────────────────────────────────────
if page == "Chat":
    st.title("💬 Chat with History")

    # render past messages
    for msg in st.session_state.chat_history:
        st.chat_message(msg["role"]).write(msg["content"])

    # input + send button via callback
    st.text_area("Enter your prompt:", key="input_area", height=150)
    st.button("Generate Text", on_click=generate_text)

    # clear history
    if st.button("🗑️ Clear History"):
        st.session_state.chat_history = []

# ── Render Image page ─────────────────────────────────────────────────
else:
    st.title("🖼️ GPT-Image-1 Generator")

    prompt = st.text_area("Image prompt:", height=100)
    size = st.selectbox("Size:", ["1024x1024", "1024x1536", "1536x1024", "auto"])
    quality = st.selectbox("Quality:", ["auto", "low", "medium", "high"])
    output_format = st.selectbox("Format:", ["png", "jpeg", "webp"])
    transparent = st.checkbox("Transparent background (png/webp only)", value=False)

    if st.button("Generate Image"):
        if not prompt:
            st.warning("Enter an image prompt.")
        else:
            params = {
                "model": "gpt-image-1",
                "prompt": prompt,
                "size": size,
                "quality": quality,
                "output_format": output_format,
                "n": 1,
            }
            if transparent:
                params["background"] = "transparent"

            with st.spinner("Generating…"):
                try:
                    result = client.images.generate(**params)
                    for img in result.data:
                        # display either b64 or URL
                        if hasattr(img, "b64_json"):
                            st.image(img.b64_json)
                        else:
                            st.image(img.url)
                except Exception as e:
                    st.error(f"API error: {e}")
