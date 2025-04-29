import streamlit as st
import matplotlib.pyplot as plt

# Set page config
st.set_page_config(page_title="I/F/C/Wise – Home", page_icon="icon.png", layout="wide")

# Generate the stylized IFCWISE logo
# YouTube video URL
youtube_url = "https://www.youtube.com/embed/yHXeL-SR2iQ?autoplay=1&mute=1&loop=1&playlist=yHXeL-SR2iQ"

# Embed YouTube video using iframe
video_html = f"""
    <iframe width="100%" height="500" src="{youtube_url}" 
    frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>
"""

st.markdown(video_html, unsafe_allow_html=True)

st.divider()

# Continue with the rest of your app
st.markdown("""
Welcome to **IFCWise**, a smart schedule automation and IFC roundtripping tool designed to help AEC professionals.

---

### What Is IFCWise?

**IFCWise** is an open-source LLM enabled smart schedule automation and IFC roundtripping tool designed to help AEC professionals.

- Extract and edit BIM schedules **without heavy software like Revit or ArchiCAD**
- Validate model data for compliance (e.g., **ISO19650**, **COBie**)
- Update IFC models from spreadsheets (**roundtrip editing**)
- Use AI to understand, transform, and fix BIM data effortlessly

---

### Who Is It For?

- BIM Managers & Coordinators  
- General Contractors  
- Architects working on public/international projects  
- MEP Engineers  
- Facility Managers & Digital Twin operators  

---

### 🔧 Key Features of IFCWise

| Feature | Description |
|--------|-------------|
| **IFC Upload** | Upload IFC files and extract schedules (quantities, types, names) |
| **Schedule Viewer** | View and filter elements with a clean web interface |
| **AI Assistant** | ChatGPT-style input to query or fix data |
| **CSV/Excel Roundtrip** | Edit offline, then re-upload for IFC updates |
| **Validation Engine** | Catch missing parameters, naming errors, or rule violations |
| **OpenBIM Friendly** | No vendor lock-in – built for interoperability |

---

You can begin by using the sidebar to import an IFC file or filter elements.

Let IFCWise streamline your openBIM workflows. 
""")
