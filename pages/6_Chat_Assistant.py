import streamlit as st
import openai
import time
import sidebar
from dotenv import load_dotenv

# Setup
st.set_page_config(page_title="I/F/C/Wise – Chat Assistant", page_icon="icon.png", layout="wide")
sidebar.sidebar_navigation()
st.title("Chat with Assistant")

# Session check
if "selected_provider" not in st.session_state or "thread_id" not in st.session_state:
    st.error("Please upload an IFC file and send it to assistant first.")
    st.stop()

provider = st.session_state["selected_provider"]
api_key = st.session_state["api_key"]

st.subheader("Ask a Question About the Model")
question = st.text_area("Type your question:")

if st.button("Ask Assistant"):
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        load_dotenv()
        openai.api_key = api_key

        try:
            # Send user message to thread
            openai.beta.threads.messages.create(
                thread_id=st.session_state["thread_id"],
                role="user",
                content=question
            )

            # Trigger assistant run
            run = openai.beta.threads.runs.create(
                thread_id=st.session_state["thread_id"],
                assistant_id=st.session_state["assistant_id"],
                instructions="Answer based on previously uploaded IFC model data. The model was sent in chunks, but all parts form a complete project."
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

            # Get the latest assistant message only
            messages = openai.beta.threads.messages.list(thread_id=st.session_state["thread_id"])
            latest_msg = next((m for m in reversed(messages.data) if m.role == "assistant"), None)

            if latest_msg:
                st.markdown(f"**Assistant:** {latest_msg.content[0].text.value}")
            else:
                st.warning("No response received.")

        except Exception as e:
            st.error(f"Failed to get assistant response: {e}")
