import streamlit as st
from openai import OpenAI

client = OpenAI()

st.set_page_config(page_title="Model Selector", layout="centered")
st.title("Chat with OpenAI Models")

# Sidebar for model selection
model_choice = st.selectbox(
    "Select a model:",
    ("gpt-4.1", "o4-mini", "o3")
)

# Text area for user prompt
user_input = st.text_area("Enter your prompt:", height=150)

# Generate button
if st.button("Generate"):  
    if not user_input:
        st.warning("Please enter a prompt to continue.")
    else:
        # Placeholder for streaming response
        response_container = st.empty()
        response_text = ""

        with st.spinner(f"Generating response using {model_choice}..."):
            try:
                response = client.responses.create(
                    model=model_choice,
                    input=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": user_input},
                    ],
                )
                response_container.markdown(response.output_text)

            except Exception as e:
                st.error(f"An error occurred: {e}")

# Footer
st.markdown("---")
st.markdown("Powered by OpenAI")
