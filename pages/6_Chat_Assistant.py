import streamlit as st
import openai
import time
import sidebar
from dotenv import load_dotenv

st.set_page_config(page_title="I/F/C/Wise – Chat Assistant", page_icon="icon.png", layout="wide")
sidebar.sidebar_navigation()

st.title("Chat with Assistant")

if "selected_provider" not in st.session_state or "thread_id" not in st.session_state:
    st.error("Please upload an IFC file and send it to assistant first.")
    st.stop()

provider = st.session_state["selected_provider"]
api_key = st.session_state["api_key"]
model_context = st.session_state.get("merged_ifc_model_data", "")

st.subheader("Ask a Question About the Model")
question = st.text_area("Type your question:")

if st.button("Ask Assistant"):
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        load_dotenv()
        openai.api_key = api_key
        try:
            openai.beta.threads.messages.create(
                thread_id=st.session_state["thread_id"],
                role="user",
                content=question
            )
            run = openai.beta.threads.runs.create(
                thread_id=st.session_state["thread_id"],
                assistant_id=st.session_state["assistant_id"],
                instructions="Answer based on uploaded IFC model data. The data has been provided in multiple chunks, but all together they form a single cohesive project model."
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
            messages = openai.beta.threads.messages.list(thread_id=st.session_state["thread_id"])
            messages_sorted = sorted(messages.data, key=lambda x: x.created_at, reverse=True)
            for i in range(0, len(messages_sorted), 2):
                if i+1 < len(messages_sorted):
                    st.markdown(f"**You:** {messages_sorted[i+1].content[0].text.value}")
                st.markdown(f"**Assistant:** {messages_sorted[i].content[0].text.value}")
                st.divider()
        except Exception as e:
            st.error(f"Failed to get assistant response: {e}")
