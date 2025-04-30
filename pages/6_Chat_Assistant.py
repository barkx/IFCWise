
import streamlit as st
import openai
import os
import time
from dotenv import load_dotenv
import sidebar

st.set_page_config(page_title="I/F/C/Wise – Chat Assistant", page_icon="icon.png", layout="wide")
sidebar.sidebar_navigation()

st.title("Chat with Assistant")

if "selected_provider" not in st.session_state or "thread_id" not in st.session_state:
    st.error("Missing assistant setup. Please return to Step 5.")
    st.stop()

api_key = st.session_state["api_key"]
openai.api_key = api_key

question = st.text_area("Ask a question about the IFC model:")

if st.button("Ask Assistant"):
    openai.beta.threads.messages.create(
        thread_id=st.session_state["thread_id"],
        role="user",
        content=question
    )
    run = openai.beta.threads.runs.create(
        thread_id=st.session_state["thread_id"],
        assistant_id=st.session_state["assistant_id"],
    )
    with st.spinner("Assistant is thinking..."):
        while True:
            status = openai.beta.threads.runs.retrieve(
                thread_id=st.session_state["thread_id"],
                run_id=run.id
            )
            if status.status == "completed":
                break
            time.sleep(1)
    messages = openai.beta.threads.messages.list(thread_id=st.session_state["thread_id"])
    last_response = next((m.content[0].text.value for m in reversed(messages.data) if m.role == "assistant"), None)
    if last_response:
        st.markdown("**Assistant Response:**")
        st.write(last_response)
