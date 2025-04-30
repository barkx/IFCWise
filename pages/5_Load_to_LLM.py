import streamlit as st
import os
import pandas as pd
import openai
import ifcopenshell
import ifcopenshell.util.element
from dotenv import load_dotenv
import sidebar
import io

# Setup Streamlit (must be first)
st.set_page_config(page_title="I/F/C/Wise – Upload to Assistant", page_icon="icon.png", layout="wide")

# Sidebar
sidebar.sidebar_navigation()

# Title
st.title("Upload Full IFC Model to Assistant")
st.write("Extracting full IFC model properties, quantities, and coordinates.")

# --- Check uploaded IFC file ---
if "ifc_path" not in st.session_state:
    st.error("No IFC file uploaded. Please complete Step 1.")
    st.stop()

ifc_path = st.session_state["ifc_path"]

try:
    ifc_model = ifcopenshell.open(ifc_path)
except Exception as e:
    st.error(f"Failed to open IFC file: {e}")
    st.stop()

# --- Extract full IFC model ---
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
        # Coordinates
        try:
            loc = e.ObjectPlacement.RelativePlacement.Location.Coordinates
            row["LocationX"], row["LocationY"], row["LocationZ"] = loc[0], loc[1], loc[2]
        except:
            row["LocationX"] = row["LocationY"] = row["LocationZ"] = ""

        # Property Sets
        try:
            psets = ifcopenshell.util.element.get_psets(e)
            for pset_name, props in psets.items():
                for key, value in props.items():
                    row[f"{pset_name}.{key}"] = value
        except:
            pass

        # Quantities
        try:
            for rel in e.IsDefinedBy:
                if rel.is_a("IfcRelDefinesByProperties"):
                    prop = rel.RelatingPropertyDefinition
                    if prop.is_a("IfcElementQuantity"):
                        for quantity in prop.Quantities:
                            q_value = getattr(quantity, "LengthValue", None) or getattr(quantity, "AreaValue", None) or getattr(quantity, "VolumeValue", None) or getattr(quantity, "HeightValue", None)
                            if q_value:
                                row[f"Quantity.{quantity.Name}"] = q_value
        except:
            pass

        data.append(row)

    return pd.DataFrame(data)

# --- Extract model now ---
with st.spinner("Extracting full IFC model..."):
    df = extract_full_ifc_data(ifc_model)

st.success(f"Extracted {len(df)} elements from IFC model.")
st.dataframe(df, use_container_width=True)

# --- Select Assistant ---
st.subheader("Select an Assistant Option")

upload_option = st.radio(
    "",
    ("Use IFCWISE ChatGPT API (default)", "Use Your Own LLM"),
    index=0,
)

provider = None
api_key = None
extra_info = {}

if upload_option == "Use Your Own LLM":
    st.divider()
    st.subheader("Provide Your LLM API Details")

    provider = st.selectbox(
        "Select your LLM Provider:",
        ("OpenAI", "Anthropic", "Azure OpenAI", "Gemini", "DeepSeek", "Ollama"),
    )

    if provider == "Azure OpenAI":
        extra_info["endpoint"] = st.text_input("Azure Endpoint")
        api_key = st.text_input("Azure API Key", type="password")
        extra_info["deployment_name"] = st.text_input("Deployment Name")
    else:
        api_key = st.text_input(f"{provider} API Key", type="password")

    if st.button("Confirm LLM Selection"):
        st.session_state["selected_provider"] = provider
        st.session_state["api_key"] = api_key
        st.session_state["extra_info"] = extra_info
        st.success(f"{provider} selected!")
else:
    st.success("Default IFCWISE ChatGPT API will be used.")
    st.session_state["selected_provider"] = "IFCWISE ChatGPT"

# --- Chunk and Upload ---
st.divider()
st.subheader("Upload Full IFC Model to Assistant")

def chunk_dataframe(df, max_lines=50):
    chunks = []
    for i in range(0, len(df), max_lines):
        chunks.append(df.iloc[i:i+max_lines])
    return chunks

if st.button("🚀 Send to Assistant"):
    with st.spinner("Sending to Assistant... Please wait."):
        chunks = chunk_dataframe(df)

        if st.session_state["selected_provider"] == "IFCWISE ChatGPT":
            load_dotenv()
            openai.api_key = os.getenv("OPENAI_API_KEY")

            assistant = openai.beta.assistants.create(
                name="IFC Assistant",
                instructions="Help users with full IFC model data uploaded as CSV.",
                model="gpt-4-turbo",
                tools=[]
            )
            thread = openai.beta.threads.create()

            st.session_state["assistant_id"] = assistant.id
            st.session_state["thread_id"] = thread.id

            for chunk in chunks:
                message = f"Here is a chunk of IFC data:\n\n{chunk.to_csv(index=False)}"
                openai.beta.threads.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=message
                )

            st.success("Uploaded to IFCWISE ChatGPT.")

        else:
            # Save merged IFC model to session for other LLM providers
            merged_text = "\n\n".join([chunk.to_csv(index=False) for chunk in chunks])
            st.session_state["merged_ifc_model_data"] = merged_text
            st.success(f"Merged IFC model stored for {st.session_state['selected_provider']}.")

    st.switch_page("pages/6_Chat_Assistant.py")
