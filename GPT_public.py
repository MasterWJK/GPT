import os
import streamlit as st
from openai import OpenAI

# ── 1) Page config ─────────────────────────────────────────────────
st.set_page_config(page_title="OpenAI Playground", layout="centered")

# ── 2) API key input ─────────────────────────────────────────────────
# Let the user enter their API key at runtime
api_key = st.sidebar.text_input(
    label="OpenAI API Key", 
    placeholder="Enter your OpenAI API key", 
    type="password"
)
if not api_key:
    st.sidebar.warning("🔑 Please enter your OpenAI API key to continue.")
    st.stop()

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

# ── 3) Sidebar navigation ─────────────────────────────────────────────
page = st.sidebar.radio("Go to:", ["Chat", "Image"])
st.sidebar.markdown("---")
st.sidebar.markdown("Powered by OpenAI")

# ── 4) Session-state defaults ────────────────────────────────────────
st.session_state.setdefault("chat_history", [])
st.session_state.setdefault("input_area", "")

# ── 5) Chat callback ─────────────────────────────────────────────────
def generate_text():
    prompt = st.session_state.input_area.strip()
    if not prompt:
        st.warning("Please enter a prompt.")
        return

    # record user message
    st.session_state.chat_history.append({"role": "user", "content": prompt})
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

    # record assistant reply
    st.session_state.chat_history.append({"role": "assistant", "content": reply})

    # clear input box
    st.session_state.input_area = ""

# ── 6) Render pages ──────────────────────────────────────────────────
if page == "Chat":
    st.title("💬 Chat with History")

    # show history
    for msg in st.session_state.chat_history:
        st.chat_message(msg["role"]).write(msg["content"])

    # input area + send button
    st.text_area("Enter your prompt:", key="input_area", height=150)
    st.button("Generate Text", on_click=generate_text)

    # clear history
    if st.button("🗑️ Clear History"):
        st.session_state.chat_history.clear()

else:
    st.title("🖼️ GPT-Image-1 Generator")
    # image inputs
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
                        if hasattr(img, "b64_json"):
                            st.image(img.b64_json)
                        else:
                            st.image(img.url)
                except Exception as e:
                    st.error(f"API error: {e}")
