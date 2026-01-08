import os
import io
import json
import base64
import pandas as pd
import streamlit as st
from PIL import Image
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

# -------------------------
# Page Config
# -------------------------
st.set_page_config(page_title="Watsonx Namecard Scanner", page_icon="📇", layout="wide")
st.title("Watsonx.ai Batch Namecard Scanner")

# Initialize Session State
if 'image_queue' not in st.session_state:
    st.session_state['image_queue'] = []  # List of dicts: {'name': str, 'bytes': bytes, 'type': str}
if 'extraction_results' not in st.session_state:
    st.session_state['extraction_results'] = [] # List of dicts with extraction data

# -------------------------
# Sidebar: Settings
# -------------------------
st.sidebar.header("Watsonx.ai Settings")
default_api_key = os.getenv("WATSONX_APIKEY", "")
default_project_id = os.getenv("WATSONX_PROJECT_ID", "")
default_url = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")

api_key = st.sidebar.text_input("IBM Cloud API Key", value=default_api_key, type="password")
project_id = st.sidebar.text_input("Project ID", value=default_project_id)
url = st.sidebar.text_input("Service URL", value=default_url)

model_id = st.sidebar.selectbox(
    "Vision Model",
    [
        "meta-llama/llama-3-2-11b-vision-instruct",
        "meta-llama/llama-3-2-90b-vision-instruct",
    ],
    index=0,
)

# -------------------------
# Helpers
# -------------------------
def detect_mime(filename: str) -> str:
    ext = (filename.split(".")[-1] or "").lower()
    if ext in ("jpg", "jpeg"): return "image/jpeg"
    if ext == "png": return "image/png"
    if ext == "bmp": return "image/bmp"
    return "image/jpeg"

def extract_namecard_json(image_bytes: bytes, mime_type: str) -> dict:
    """Sends image to watsonx.ai and returns parsed JSON."""
    credentials = {"url": url, "apikey": api_key}
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    
    prompt_text = (
        "You are given a business card image.\n"
        "Extract information and return STRICT JSON ONLY, with exactly these keys:\n"
        '{\n'
        ' "Company Name": string|null,\n'
        ' "Name": string|null,\n'
        ' "Title": string|null,\n'
        ' "Phone Number": string|null,\n'
        ' "Email Address": string|null,\n'
        ' "Company Address": string|null,\n'
        ' "Company Website": string|null\n'
        '}\n'
        "Rules:\n"
        "- No markdown, no code blocks, no explanation.\n"
        "- If missing, use null.\n"
    )

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{image_b64}"},
                },
                {"type": "text", "text": prompt_text},
            ],
        }
    ]

    params = {
        GenParams.MAX_NEW_TOKENS: 500,
        GenParams.TEMPERATURE: 0.0,
        GenParams.TOP_P: 1.0,
        GenParams.TOP_K: 50,
    }

    model = ModelInference(
        model_id=model_id,
        credentials=credentials,
        project_id=project_id,
        params=params,
    )

    response = model.chat(messages=messages)
    content = response["choices"][0]["message"]["content"]
    cleaned = content.replace("```json", "").replace("```", "").strip()
    return json.loads(cleaned)

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

def update_result(index, key):
    """Callback to update session state when user edits a field"""
    st.session_state['extraction_results'][index][key] = st.session_state[f"{key}_{index}"]

# -------------------------
# UI: Tabs
# -------------------------
tab1, tab2, tab3 = st.tabs(["Upload", "Extract", "Export"])

# =========================
# Tab 1: Upload
# =========================
with tab1:
    st.header("Upload Images")
    
    # Toggle for input method
    input_method = st.radio("Choose Input Method:", ["Upload Files", "Use Camera"], horizontal=True)
    
    if input_method == "Upload Files":
        uploaded_files = st.file_uploader(
            "Select images (Batch supported)",
            type=["png", "jpg", "jpeg", "bmp"],
            accept_multiple_files=True
        )
        if uploaded_files:
            # Add unique files to queue
            current_names = {img['name'] for img in st.session_state['image_queue']}
            for f in uploaded_files:
                if f.name not in current_names:
                    st.session_state['image_queue'].append({
                        'name': f.name,
                        'bytes': f.getvalue(),
                        'type': detect_mime(f.name)
                    })
    
    elif input_method == "Use Camera":
        camera_file = st.camera_input("Take a picture")
        if camera_file:
            # Generate a unique name for camera captures
            import time
            cam_name = f"camera_{int(time.time())}.jpg"
            # Avoid duplicate adds if the user hasn't retaken the photo
            current_names = {img['name'] for img in st.session_state['image_queue']}
            if cam_name not in current_names:
                st.session_state['image_queue'].append({
                    'name': cam_name,
                    'bytes': camera_file.getvalue(),
                    'type': "image/jpeg"
                })
                st.success("Photo added to queue!")

    # Display Queue
    if st.session_state['image_queue']:
        st.divider()
        st.subheader(f"Images in Queue ({len(st.session_state['image_queue'])})")
        
        # Grid view of uploaded images
        cols = st.columns(4)
        for i, img_data in enumerate(st.session_state['image_queue']):
            with cols[i % 4]:
                st.image(img_data['bytes'], caption=img_data['name'], use_column_width=True)
        
        if st.button("Clear Queue", type="secondary"):
            st.session_state['image_queue'] = []
            st.rerun()
    else:
        st.info("No images in queue. Please upload files or use the camera.")

# =========================
# Tab 2: Extract
# =========================
with tab2:
    st.header("Extract & Edit Information")
    
    queue = st.session_state['image_queue']
    can_run = bool(api_key and project_id and url and queue)
    
    if not queue:
        st.warning("Please add images in the 'Upload' tab first.")
    
    # Process Button
    if st.button("Start Extraction", type="primary", disabled=not can_run):
        results = []
        progress_bar = st.progress(0.0)
        status = st.empty()
        
        for idx, img_data in enumerate(queue, start=1):
            status.write(f"Processing: {img_data['name']}...")
            try:
                data = extract_namecard_json(img_data['bytes'], img_data['type'])
                row = {
                    "File Name": img_data['name'],
                    "Company Name": data.get("Company Name"),
                    "Name": data.get("Name"),
                    "Title": data.get("Title"),
                    "Phone Number": data.get("Phone Number"),
                    "Email Address": data.get("Email Address"),
                    "Company Address": data.get("Company Address"),
                    "Company Website": data.get("Company Website"),
                    "image_bytes": img_data['bytes'] # Store for display
                }
            except Exception as e:
                row = {
                    "File Name": img_data['name'],
                    "Company Name": "", "Name": "", "Title": "",
                    "Phone Number": "", "Email Address": "",
                    "Company Address": "", "Company Website": "",
                    "image_bytes": img_data['bytes'],
                    "Error": str(e)
                }
            results.append(row)
            progress_bar.progress(idx / len(queue))
            
        st.session_state['extraction_results'] = results
        progress_bar.empty()
        status.success("Extraction Complete! You can edit the results below.")

    # Editable Interface
    if st.session_state['extraction_results']:
        st.divider()
        st.write("Review and edit the extracted information below. Changes are saved automatically.")
        
        for i, row in enumerate(st.session_state['extraction_results']):
            with st.container():
                c1, c2 = st.columns([1, 2])
                
                # Column 1: Image
                with c1:
                    st.image(row['image_bytes'], caption=row['File Name'], use_column_width=True)
                
                # Column 2: Editable Fields
                with c2:
                    st.subheader(f"Card {i+1}")
                    
                    # Layout fields in a grid for compactness
                    f1, f2 = st.columns(2)
                    with f1:
                        st.text_input("Name", value=row['Name'], key=f"Name_{i}", on_change=update_result, args=(i, 'Name'))
                        st.text_input("Title", value=row['Title'], key=f"Title_{i}", on_change=update_result, args=(i, 'Title'))
                        st.text_input("Phone", value=row['Phone Number'], key=f"Phone Number_{i}", on_change=update_result, args=(i, 'Phone Number'))
                        st.text_input("Email", value=row['Email Address'], key=f"Email Address_{i}", on_change=update_result, args=(i, 'Email Address'))
                    
                    with f2:
                        st.text_input("Company", value=row['Company Name'], key=f"Company Name_{i}", on_change=update_result, args=(i, 'Company Name'))
                        st.text_input("Website", value=row['Company Website'], key=f"Company Website_{i}", on_change=update_result, args=(i, 'Company Website'))
                        st.text_area("Address", value=row['Company Address'], key=f"Company Address_{i}", on_change=update_result, args=(i, 'Company Address'), height=100)
                
                st.divider()

# =========================
# Tab 3: Export
# =========================
with tab3:
    st.header("Export Data")
    
    if st.session_state['extraction_results']:
        # Convert list of dicts to DataFrame, excluding internal 'image_bytes' column
        export_data = []
        for row in st.session_state['extraction_results']:
            # Create a clean copy without the image bytes for CSV/Excel
            clean_row = {k: v for k, v in row.items() if k != 'image_bytes'}
            export_data.append(clean_row)
            
        df = pd.DataFrame(export_data)
        
        st.subheader("Final Dataset")
        st.dataframe(df, use_container_width=True) # Shows ALL rows
        
        # Download Buttons
        col1, col2, col3 = st.columns(3)
        
        csv = df.to_csv(index=False).encode('utf-8')
        json_str = df.to_json(orient='records', indent=2)
        
        with col1:
            try:
                excel_data = to_excel(df)
                st.download_button("Download Excel", data=excel_data, file_name="cards.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            except Exception as e:
                st.error(f"Excel export failed (missing openpyxl?): {e}")
        
        with col2:
            st.download_button("Download CSV", data=csv, file_name="cards.csv", mime="text/csv")
            
        with col3:
            st.download_button("Download JSON", data=json_str, file_name="cards.json", mime="application/json")
    else:
        st.info("No data to export.")
