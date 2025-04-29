import streamlit as st

st.set_page_config(page_title="I/F/C/Wise – IFC Info", page_icon="icon.png", layout="wide")

import sidebar
import ifcopenshell
import os
import datetime
import pandas as pd
import tempfile

sidebar.sidebar_navigation()

st.title("IFC Model Information")

# Check IFC upload
if "ifc_path" not in st.session_state:
    st.error("No IFC file uploaded. Please go back to Step 1 and upload an IFC file first.")
    st.stop()

ifc_path = st.session_state["ifc_path"]

if not os.path.exists(ifc_path):
    st.error("IFC file not found. Please re-upload the IFC file.")
    st.stop()

# Load IFC
try:
    ifc_model = ifcopenshell.open(ifc_path)
    st.success(f"Loaded IFC file: `{os.path.basename(ifc_path)}`")
except Exception as e:
    st.error(f"Failed to open IFC file: {e}")
    st.stop()

# ---- PART 1: IFC FILE INFO ----
st.divider()
st.markdown("### IFC File Info")

file_size_kb = os.path.getsize(ifc_path) / 1024

# Try getting creation date
creation_date = "N/A"
project = ifc_model.by_type("IfcProject")
if project:
    project = project[0]
    if hasattr(project, 'OwnerHistory') and project.OwnerHistory:
        try:
            created_timestamp = project.OwnerHistory.CreationDate
            creation_date = datetime.datetime.utcfromtimestamp(created_timestamp).strftime('%Y-%m-%d')
        except Exception:
            pass

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown("**File Name:**")
    st.write(f"`{os.path.basename(ifc_path)}`")
with col2:
    st.markdown("**File Size:**")
    st.write(f"{file_size_kb:.2f} KB")
with col3:
    st.markdown("**IFC Schema:**")
    st.write(ifc_model.schema)
with col4:
    st.markdown("**Creation Date:**")
    st.write(creation_date)

# ---- PART 2: SITE & BUILDING INFO ----
st.divider()
st.markdown("### Site and Building Info")

sites = ifc_model.by_type("IfcSite")
buildings = ifc_model.by_type("IfcBuilding")
storeys = ifc_model.by_type("IfcBuildingStorey")

col5, col6, col7 = st.columns(3)
col5.metric("Sites", len(sites))
col6.metric("Buildings", len(buildings))
col7.metric("Storeys", len(storeys))

# ---- PART 3: ELEMENT INFO ----
st.divider()
st.markdown("### Element Info")

all_elements = ifc_model.by_type("IfcProduct")
element_counts = {}

for element in all_elements:
    type_name = element.is_a()
    element_counts[type_name] = element_counts.get(type_name, 0) + 1

total_elements = sum(element_counts.values())

st.markdown(f"**Total Number of Elements:** {total_elements}")

if element_counts:
    element_data = pd.DataFrame(
        sorted(element_counts.items(), key=lambda x: x[1], reverse=True),
        columns=["Element Type", "Quantity"]
    )
else:
    element_data = pd.DataFrame(columns=["Element Type", "Quantity"])
    st.info("No IFC elements found in this file.")

# ---- ADVANCED: SEARCH IFC ELEMENTS ----
st.divider()
st.markdown("### Search in IFC Elements")

# Extract more detailed data
def extract_ifc_data(path, basic=True, coords=True, psets=False, quants=False):
    ifc = ifcopenshell.open(path)
    elements = ifc.by_type("IfcProduct")
    data = []
    for e in elements:
        row = {}
        if basic:
            row.update({
                "GlobalId": getattr(e, "GlobalId", ""),
                "ElementType": e.is_a(),
                "Name": getattr(e, "Name", ""),
                "ObjectType": getattr(e, "ObjectType", ""),
                "Description": getattr(e, "Description", ""),
                "PredefinedType": getattr(e, "PredefinedType", "") if hasattr(e, "PredefinedType") else ""
            })
        if coords:
            try:
                loc = e.ObjectPlacement.RelativePlacement.Location.Coordinates
                row["LocationX"], row["LocationY"], row["LocationZ"] = loc[0], loc[1], loc[2]
            except:
                row["LocationX"] = row["LocationY"] = row["LocationZ"] = ""
        data.append(row)
    return pd.DataFrame(data)

detailed_df = extract_ifc_data(st.session_state["ifc_path"])

# Search functionality
search_term = st.text_input("Search by GlobalId, Name, Type, or ObjectType")

if search_term:
    filtered_df = detailed_df[
        detailed_df.apply(lambda row: search_term.lower() in str(row).lower(), axis=1)
    ]
else:
    filtered_df = detailed_df

st.dataframe(filtered_df, use_container_width=True)

# Save for next steps
if not filtered_df.empty:
    st.session_state["filtered_csv_data"] = filtered_df.to_csv(index=False)

# ---- COLLAPSIBLE: FILTER BY ELEMENTS ----
with st.expander("Filter by Elements", expanded=False):
    st.write("**Filter IFC elements by type**")
    types = sorted(detailed_df["ElementType"].dropna().unique())
    selected_types = st.multiselect("Select Element Types", types, default=types)

    df_element_filtered = detailed_df[detailed_df["ElementType"].isin(selected_types)]
    st.dataframe(df_element_filtered, use_container_width=True)

    if not df_element_filtered.empty:
        st.session_state["csv_path_element_filtered"] = df_element_filtered.to_csv(index=False)

# ---- COLLAPSIBLE: FILTER BY ATTRIBUTES ----
with st.expander("Filter by Attributes", expanded=False):
    st.write("**Select specific attributes to display.**")
    all_columns = list(detailed_df.columns)
    selected_columns = st.multiselect("Choose Attributes", all_columns, default=["GlobalId", "Name", "ElementType"])

    if selected_columns:
        df_attribute_filtered = detailed_df[selected_columns]
        st.dataframe(df_attribute_filtered, use_container_width=True)

        if not df_attribute_filtered.empty:
            st.session_state["csv_path_attribute_filtered"] = df_attribute_filtered.to_csv(index=False)

# ---- COLLAPSIBLE: EXPORT DATA ----
with st.expander("Export Data", expanded=False):
    st.write("**Export IFC data into different formats.**")
    export_format = st.selectbox("Select Export Format:", ["CSV", "Excel", "JSON"])

    if export_format == "CSV":
        csv_data = detailed_df.to_csv(index=False)
        st.download_button("Download CSV", csv_data, file_name="ifc_data.csv", mime="text/csv")
    elif export_format == "Excel":
        excel_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        detailed_df.to_excel(excel_file.name, index=False)
        with open(excel_file.name, 'rb') as f:
            st.download_button("Download Excel", f, file_name="ifc_data.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    elif export_format == "JSON":
        json_data = detailed_df.to_json(orient="records", indent=4)
        st.download_button("Download JSON", json_data, file_name="ifc_data.json", mime="application/json")

# ---- NEXT ACTIONS ----
st.divider()
col8, col9, col10 = st.columns(3)

with col8:
    if st.button("Load to LLM"):
        if "filtered_csv_data" in st.session_state:
            st.switch_page("pages/5_Load_to_LLM.py")
        else:
            st.warning("No element data available to load.")
