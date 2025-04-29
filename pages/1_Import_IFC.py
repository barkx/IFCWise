import streamlit as st
import sidebar
import uuid
import ifcopenshell
import os
import tempfile

st.set_page_config(page_title="I/F/C/Wise – Import IFC", page_icon="icon.png", layout="wide")

sidebar.sidebar_navigation()

st.title("Import or Select IFC Project")

# --- Option 1: Upload your own IFC ---
st.subheader("Option 1: Upload Your Own IFC File")

uploaded_file = st.file_uploader("Upload your IFC file", type=["ifc"])

if uploaded_file:
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())

    # Save uploaded IFC file path to session
    st.session_state["ifc_path"] = file_path
    st.success("IFC file uploaded and saved.")

    # Automatically move to Step 2 after upload
    st.switch_page("pages/2_Info.py")  # Corrected here

# --- Divider ---
st.divider()

# --- Option 2: Select a demo project ---
st.subheader("Option 2: Select a Demo Project")

demo_projects = [
    {
        "name": "Small Project Sample",
        "description": "671 KB",
        "image": "demo_images/1.png",
        "path": "demo_ifc/1.ifc"
    },
    {
        "name": "Medium Project Sample",
        "description": "2.325 KB",
        "image": "demo_images/2.png",
        "path": "demo_ifc/2.ifc"
    },
    {
        "name": "Large Project Sample",
        "description": "20.385 KB",
        "image": "demo_images/3.png",
        "path": "demo_ifc/3.ifc"
    },
]

cols = st.columns(3)

for i, project in enumerate(demo_projects):
    with cols[i % 3]:
        st.image(project["image"], use_container_width=True)
        st.markdown(f"**{project['name']}**")
        st.caption(project["description"])
        if st.button(f"Select '{project['name']}'", key=f"select_{i}"):
            st.session_state["ifc_path"] = project["path"]
            st.success(f"Selected project: {project['name']}")
            st.switch_page("pages/2_Info.py")  # Corrected here


