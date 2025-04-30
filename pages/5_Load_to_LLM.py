
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
st.write("Send your IFC model in structured chunks to the Assistant using gpt-4-turbo.")

if "ifc_path" not in st.session_state:
    st.error("No IFC file uploaded. Please complete Step 1.")
    st.stop()

ifc_path = st.session_state["ifc_path"]
ifc_model = ifcopenshell.open(ifc_path)

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

df = extract_full_ifc_data(ifc_model)
st.dataframe(df, use_container_width=True)

provider = "OpenAI"
st.session_state["selected_provider"] = provider
api_key = st.text_input("Enter your OpenAI API key:", type="password")
if st.button("Confirm"):
    st.session_state["api_key"] = api_key
    st.success("API key saved.")

def chunk_dataframe(df, max_rows=50):
    return [df.iloc[i:i+max_rows] for i in range(0, len(df), max_rows)]

if st.button("Send to Assistant"):
    load_dotenv()
    openai.api_key = api_key
    assistant = openai.beta.assistants.create(
        name="IFC Assistant",
        instructions="Use all chunks as one IFC model. Only return responses based on this context.",
        model="gpt-4-turbo",
        tools=[]
    )
    thread = openai.beta.threads.create()
    st.session_state["assistant_id"] = assistant.id
    st.session_state["thread_id"] = thread.id

    chunks = chunk_dataframe(df)
    for i, chunk in enumerate(chunks):
        csv_data = chunk.to_csv(index=False)
        openai.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"IFC Model Chunk {i+1}:

{csv_data}"
        )
        time.sleep(1.5)

    st.success(f"Uploaded {len(chunks)} chunks to Assistant.")
    st.switch_page("pages/6_Chat_Assistant.py")
