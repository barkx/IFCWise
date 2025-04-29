import streamlit as st
import os
import pandas as pd
import openai
import ifcopenshell
import ifcopenshell.util.element
from dotenv import load_dotenv
import sidebar
import time

# Setup Streamlit
st.set_page_config(page_title="I/F/C/Wise – Upload to Assistant", page_icon="icon.png", layout="wide")

# Sidebar
sidebar.sidebar_navigation()

st.title("Upload Full IFC Model to Assistant")
st.write("This will send all elements from the IFC file to the assistant in structured batches.")

# --- Validate IFC file ---
if "ifc_path" not in st.session_state:
    st.error("No IFC file uploaded. Please complete Step 1.")
    st.stop()

ifc_path = st.session_state["ifc_path"]

try:
    ifc_model = ifcopenshell.open(ifc_path)
except Exception as e:
    st.error(f"Failed to open IFC file: {e}")
    st.stop()

# --- Extract full IFC model data ---
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

# --- Load model into DataFrame ---
with st.spinner("Extracting elements from IFC model..."):
    df = extract_full_ifc_data(ifc_model)

st.success(f"Extracted {len(df)} elements.")
st.dataframe(df, use_container_width=True)

# --- LLM Provider Config ---
st.subheader("Connect Your Own Assistant")

provider = st.selectbox(
    "Select your LLM Provider:",
    ("OpenAI", "Anthropic", "Azure OpenAI", "Gemini", "DeepSeek", "Ollama"),
)

api_key = ""
extra_info = {}

if provider == "Azure OpenAI":
    extra_info["endpoint"] = st.text_input("Azure Endpoint")
    api_key = st.text_input("Azure API Key", type="password")
    extra_info["deployment_name"] = st.text_input("Deployment Name")
else:
    api_key = st.text_input(f"{provider} API Key", type="password")

if st.button("Confirm LLM Setup"):
    st.session_state["selected_provider"] = provider
    st.session_state["api_key"] = api_key
    st.session_state["extra_info"] = extra_info
    st.success(f"{provider} selected.")

# --- Chunking logic by type ---
def chunk_dataframe_by_type(df, max_rows_per_chunk=50):
    chunks = []
    grouped = df.groupby("ElementType")
    for element_type, group_df in grouped:
        num_chunks = (len(group_df) - 1) // max_rows_per_chunk + 1
        for i in range(0, len(group_df), max_rows_per_chunk):
            chunk_df = group_df.iloc[i:i+max_rows_per_chunk]
            header = f"[{element_type}] – Chunk {i // max_rows_per_chunk + 1} of {num_chunks}"
            chunk_csv = chunk_df.to_csv(index=False)
            chunks.append((header, chunk_csv))
    return chunks

# --- Upload process ---
st.divider()
st.subheader("Upload to Assistant")

if st.button("Send to Assistant"):
    if not api_key:
        st.error("Please enter your API key first.")
        st.stop()

    with st.spinner("Sending all data to assistant..."):
        chunks = chunk_dataframe_by_type(df, max_rows_per_chunk=50)
        full_text = "\n\n".join([f"{header}\n\n{csv}" for header, csv in chunks])

        st.session_state["merged_ifc_model_data"] = full_text
        st.success(f"IFC model data prepared for {provider}.")

    st.switch_page("pages/6_Chat_Assistant.py")
