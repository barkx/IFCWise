import streamlit as st
import requests
import openai
import os
import time
from dotenv import load_dotenv
import sidebar

# Setup Streamlit
st.set_page_config(page_title="I/F/C/Wise – Chat Assistant", page_icon="icon.png", layout="wide")

# Sidebar
sidebar.sidebar_navigation()

# Title
st.title("Chat with Assistant")

# Check session state
if "selected_provider" not in st.session_state:
    st.error("Please upload an IFC file first (Step 1).")
    st.stop()

provider = st.session_state["selected_provider"]
st.caption(f"Assistant powered by: **{provider}**")

model_context = st.session_state.get("merged_ifc_model_data", "")

# Ask a question
st.subheader("Ask a Question About the Model")
question = st.text_area("Type your question:")

if st.button("Ask Assistant"):
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        if provider == "IFCWISE ChatGPT":
            load_dotenv()
            openai.api_key = os.getenv("OPENAI_API_KEY")

            openai.beta.threads.messages.create(
                thread_id=st.session_state["thread_id"],
                role="user",
                content=question
            )

            run = openai.beta.threads.runs.create(
                thread_id=st.session_state["thread_id"],
                assistant_id=st.session_state["assistant_id"],
                instructions="Answer based on uploaded IFC model data."
            )

            with st.spinner("Waiting for assistant to respond..."):
                while True:
                    status = openai.beta.threads.runs.retrieve(
                        thread_id=st.session_state["thread_id"],
                        run_id=run.id
                    )
                    if status.status == "completed":
                        break
                    time.sleep(1)

            # Get and show response
            messages = openai.beta.threads.messages.list(thread_id=st.session_state["thread_id"])
            messages_sorted = sorted(messages.data, key=lambda x: x.created_at, reverse=True)

            i = 0
            while i < len(messages_sorted):
                msg = messages_sorted[i]
                if msg.role == "assistant" and i + 1 < len(messages_sorted) and messages_sorted[i + 1].role == "user":
                    user_msg = messages_sorted[i + 1]
                    assistant_msg = msg

                    with st.container():
                        st.markdown(f"**You:** {user_msg.content[0].text.value}")
                        st.markdown(f"**Assistant:** {assistant_msg.content[0].text.value}")
                    st.divider()
                    i += 2
                else:
                    i += 1

        else:
            # Manual API logic for external LLMs
            api_key = st.session_state.get("api_key")
            extra = st.session_state.get("extra_info", {})
            final_prompt = f"You have received the following IFC model data:\n\n{model_context}\n\nNow answer this question:\n{question}"
            answer = ""

            try:
                if provider == "Anthropic":
                    url = "https://api.anthropic.com/v1/messages"
                    headers = {
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "model": "claude-3-opus-20240229",
                        "messages": [{"role": "user", "content": final_prompt}],
                        "max_tokens": 1000
                    }
                    response = requests.post(url, headers=headers, json=payload)
                    answer = response.json().get("content", [{}])[0].get("text", str(response.json()))

                elif provider == "Gemini":
                    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "contents": [{"parts": [{"text": final_prompt}]}]
                    }
                    response = requests.post(url, headers=headers, json=payload)
                    answer = response.json()["candidates"][0]["content"]["parts"][0]["text"]

                elif provider == "OpenAI":
                    url = "https://api.openai.com/v1/chat/completions"
                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "model": "gpt-4",
                        "messages": [{"role": "user", "content": final_prompt}]
                    }
                    response = requests.post(url, headers=headers, json=payload)
                    answer = response.json()["choices"][0]["message"]["content"]

                else:
                    answer = "Provider not supported yet."

            except Exception as e:
                answer = f"Failed to get response: {e}"

            st.markdown(f"**You:** {question}")
            st.markdown(f"**{provider}:** {answer}")

# Navigation to Modify Assistant
# st.divider()
# st.subheader("Ready to Modify the Model?")
# if st.button("Go to Modify Assistant"):
#     st.switch_page("pages/7_Modify_Assistant.py")
