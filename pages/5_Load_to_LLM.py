import streamlit as st
import os
import pandas as pd
import openai
import ifcopenshell
import ifcopenshell.util.element
from dotenv import load_dotenv
import sidebar
import time

st.set_page_config(page_title="I/F/C/Wise – Upload to Assistant", page_icon="icon.png", layout="wide")
sidebar.sidebar_navigation()

st.title("Upload Full IFC Model to Assistant")

if "ifc_path" not in st.session_state:
    st.error("No IFC file uploaded. Please complete Step 1.")
    st.stop()

ifc_path = st.session_state["ifc_path"]

try:
    ifc_model = ifcopenshell.open(ifc_path)
except Exception as e:
    st.error(f"Failed to open IFC file: {e}")
    st.stop()

def extract_full_ifc_data(ifc_model):
    elements = ifc_model.by_type("IfcProduct")
    data = []
    for e in elements:
        row = {
            "ElementType": e.is_a(),
            "GlobalId": e.GlobalId,
            "Name": getattr(e, "Name", ""),
            "ObjectType": getattr(e, "ObjectType", ""),
            "Description": getattr(e, "Description", ""),
            "PredefinedType": getattr(e, "PredefinedType", "") if hasattr(e, "PredefinedType") else "",
        }
        try:
            loc = e.ObjectPlacement.RelativePlacement.Location.Coordinates
            row["LocationX"], row["LocationY"], row["LocationZ"] = loc[0], loc[1], loc[2]
        except:
            row["LocationX"] = row["LocationY"] = row["LocationZ"] = ""
        try:
            psets = ifcopenshell.util.element.get_psets(e)
            for pset_name, props in psets.items():
                for key, value in props.items():
                    row[f"{pset_name}.{key}"] = value
        except:
            pass
        try:
            for rel in e.IsDefinedBy:
                if rel.is_a("IfcRelDefinesByProperties"):
                    prop = rel.RelatingPropertyDefinition
                    if prop.is_a("IfcElementQuantity"):
                        for quantity in prop.Quantities:
                            q_val = (
                                getattr(quantity, "LengthValue", None)
                                or getattr(quantity, "AreaValue", None)
                                or getattr(quantity, "VolumeValue", None)
                                or getattr(quantity, "HeightValue", None)
                            )
                            if q_val is not None:
                                row[f"Quantity.{quantity.Name}"] = q_val
        except:
            pass
        data.append(row)
    return pd.DataFrame(data)

with st.spinner("Extracting elements from IFC model..."):
    df = extract_full_ifc_data(ifc_model)

st.success(f"Extracted {len(df)} elements.")
st.dataframe(df, use_container_width=True)

st.subheader("Connect Your Own Assistant")
provider = st.selectbox("Select your LLM Provider:", ("OpenAI", "Anthropic", "Azure OpenAI", "Gemini", "DeepSeek", "Ollama"))
api_key = st.text_input("API Key", type="password")
extra_info = {}

if provider == "Azure OpenAI":
    extra_info["endpoint"] = st.text_input("Azure Endpoint")
    extra_info["deployment_name"] = st.text_input("Deployment Name")

if st.button("Confirm LLM Setup"):
    st.session_state["selected_provider"] = provider
    st.session_state["api_key"] = api_key
    st.session_state["extra_info"] = extra_info
    st.success(f"{provider} configured.")

def chunk_dataframe_by_type(df, max_tokens=8000):
    def estimate_tokens(text: str) -> int:
        return int(len(text.encode("utf-8")) / 4)

    chunks = []
    grouped = df.groupby("ElementType")
    for element_type, group_df in grouped:
        current_chunk = []
        current_tokens = 0
        chunk_id = 1
        for _, row in group_df.iterrows():
            csv_line = ",".join([str(v) for v in row.values]) + "\n"
            tokens = estimate_tokens(csv_line)
            if current_tokens + tokens > max_tokens:
                csv_data = "".join(current_chunk)
                header = f"[{element_type}] – Chunk {chunk_id}"
                chunks.append((header, csv_data))
                current_chunk = []
                current_tokens = 0
                chunk_id += 1
            current_chunk.append(csv_line)
            current_tokens += tokens
        if current_chunk:
            header = f"[{element_type}] – Chunk {chunk_id}"
            csv_data = "".join(current_chunk)
            chunks.append((header, csv_data))
    return chunks

if st.button("Send to Assistant"):
    if not api_key:
        st.error("Please enter your API key first.")
        st.stop()
    with st.spinner("Preparing and sending model to assistant..."):
        load_dotenv()
        openai.api_key = api_key
        header_line = ",".join(df.columns) + "\n"
        chunks = chunk_dataframe_by_type(df)
        full_chunks = [(h, header_line + c) for h, c in chunks]
        st.session_state["merged_ifc_model_data"] = "\n\n".join([f"{h}\n\n{c}" for h, c in full_chunks])
        assistant = openai.beta.assistants.create(
            name="IFC Assistant",
            instructions="You will receive structured data in multiple CSV chunks. Treat all chunks as one IFC model. Do not assume missing context.",
            model="gpt-4-turbo",
            tools=[]
        )
        thread = openai.beta.threads.create()
        st.session_state["assistant_id"] = assistant.id
        st.session_state["thread_id"] = thread.id
        for i, (header, chunk) in enumerate(full_chunks):
            st.write(f"Sending chunk {i+1} of {len(full_chunks)}: {header}")
            openai.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=f"{header}\n\n{chunk}"
            )
            time.sleep(1.5)
        st.success("All chunks successfully uploaded to assistant.")
        st.switch_page("pages/6_Chat_Assistant.py")
