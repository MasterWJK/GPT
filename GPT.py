import streamlit as st
from openai import OpenAI

client = OpenAI()

st.set_page_config(page_title="Model & Image Playground", layout="centered")
st.title("Chat with OpenAI Models or Generate Images")

mode = st.radio("Mode:", ["Chat", "Image"])

if mode == "Chat":
    model_choice = st.selectbox("Select a model:", ("gpt-4.1", "o4-mini", "o3"))
    user_input = st.text_area("Enter your prompt:", height=150)
    if st.button("Generate Text"):
        if not user_input:
            st.warning("Please enter a prompt to continue.")
        else:
            with st.spinner(f"Generating response using {model_choice}..."):
                try:
                    response = client.responses.create(
                        model=model_choice,
                        input=[
                            {"role": "system", "content": "You are a helpful assistant."},
                            {"role": "user", "content": user_input},
                        ],
                    )
                    st.markdown(response.output_text)
                except Exception as e:
                    st.error(f"An error occurred: {e}")

elif mode == "Image":
    image_prompt = st.text_area("Enter image prompt:", height=100)
    num_images = st.slider("Number of images", 1, 4, 1)
    size = st.selectbox("Image size", ["256x256", "512x512", "1024x1024"])
    if st.button("Generate Image"):
        if not image_prompt:
            st.warning("Please describe the image you want.")
        else:
            with st.spinner("Generating images…"):
                try:
                    result = client.images.generate(
                        model="dall-e-3",
                        prompt=image_prompt,
                        n=num_images,
                        size=size,
                    )
                    for img in result.data:
                        st.image(img.url)
                except Exception as e:
                    st.error(f"An error occurred: {e}")

st.markdown("---")
st.markdown("Powered by OpenAI")
