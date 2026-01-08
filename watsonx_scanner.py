import os
import io
import json
import base64
import pandas as pd
import streamlit as st
from PIL import Image
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

# Page Configuration
st.set_page_config(page_title="Watsonx Namecard Scanner", page_icon="📇", layout="wide")
st.title("Watsonx.ai Batch Namecard Scanner")

# -------------------------
# Sidebar: watsonx settings
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
st.sidebar.caption("Tip: Keep the API Key secret.")

# -------------------------
# Helpers
# -------------------------
def file_to_base64(uploaded_file) -> str:
    """Convert uploaded file to base64 string."""
    return base64.b64encode(uploaded_file.getvalue()).decode("utf-8")

def detect_mime(filename: str) -> str:
    """Detect mime type based on extension."""
    ext = (filename.split(".")[-1] or "").lower()
    if ext in ("jpg", "jpeg"): return "image/jpeg"
    if ext == "png": return "image/png"
    if ext == "bmp": return "image/bmp"
    return "image/jpeg"

def extract_namecard_json(image_b64: str, mime_type: str) -> dict:
    """Sends image to watsonx.ai and returns parsed JSON."""
    credentials = {"url": url, "apikey": api_key}
    
    # Updated prompt to match specific requested fields
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
    """Convert dataframe to excel bytes."""
    output = io.BytesIO()
    # Requires openpyxl installed
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

# -------------------------
# UI: Tabs Structure
# -------------------------

# Initialize session state for results
if 'extraction_results' not in st.session_state:
    st.session_state['extraction_results'] = None

tab1, tab2, tab3 = st.tabs(["Upload", "Extract", "Export"])

# =========================
# Tab 1: Upload
# =========================
with tab1:
    st.header("Upload Images")
    st.write("Upload business card images via file selection or camera.")
    
    # File Uploader
    uploaded_files = st.file_uploader(
        "Upload Files (Batch supported)",
        type=["png", "jpg", "jpeg", "bmp"],
        accept_multiple_files=True,
        key="uploader"
    )
    
    # Camera Input
    camera_image = st.camera_input("Using Camera", key="camera")
    
    # Combine inputs for processing logic
    current_files = []
    if uploaded_files:
        current_files.extend(uploaded_files)
    if camera_image:
        current_files.append(camera_image)
        
    if current_files:
        st.success(f"Ready to process {len(current_files)} image(s). Please go to the 'Extract' tab.")
        with st.expander("Preview Selected Images", expanded=False):
            cols = st.columns(3)
            for i, f in enumerate(current_files):
                img = Image.open(io.BytesIO(f.getvalue()))
                cols[i % 3].image(img, caption=f.name, width=200)
    else:
        st.info("Waiting for image upload...")

# =========================
# Tab 2: Extract
# =========================
with tab2:
    st.header("Extract Information")
    
    # Re-gather files from Tab 1 widgets
    files_to_process = []
    if uploaded_files: files_to_process.extend(uploaded_files)
    if camera_image: files_to_process.append(camera_image)
    
    can_run = bool(api_key and project_id and url and files_to_process)
    
    if not files_to_process:
        st.warning("No images found. Please upload or take a photo in the 'Upload' tab.")
    elif not (api_key and project_id and url):
        st.warning("Please configure Watsonx settings in the sidebar.")
    
    if st.button("Start Extraction", type="primary", disabled=not can_run):
        results = []
        progress_bar = st.progress(0.0)
        status_text = st.empty()
        
        for idx, f in enumerate(files_to_process, start=1):
            status_text.write(f"Processing: {f.name} ({idx}/{len(files_to_process)})")
            try:
                b64 = file_to_base64(f)
                mime = detect_mime(f.name)
                data = extract_namecard_json(b64, mime)
                
                # Normalize keys
                row = {
                    "File Name": f.name,
                    "Company Name": data.get("Company Name") or data.get("Company"),
                    "Name": data.get("Name"),
                    "Title": data.get("Title"),
                    "Phone Number": data.get("Phone Number") or data.get("Phone"),
                    "Email Address": data.get("Email Address") or data.get("Email"),
                    "Company Address": data.get("Company Address") or data.get("Address"),
                    "Company Website": data.get("Company Website") or data.get("Website"),
                    "Error": None
                }
            except Exception as e:
                row = {
                    "File Name": f.name,
                    "Company Name": None, "Name": None, "Title": None,
                    "Phone Number": None, "Email Address": None,
                    "Company Address": None, "Company Website": None,
                    "Error": str(e)
                }
            results.append(row)
            progress_bar.progress(idx / len(files_to_process))
            
        progress_bar.empty()
        status_text.success("Extraction Complete!")
        
        # Save to session state
        st.session_state['extraction_results'] = pd.DataFrame(results)

    # Show results if they exist in session state
    if st.session_state['extraction_results'] is not None:
        st.subheader("Extraction Results")
        st.dataframe(st.session_state['extraction_results'], use_container_width=True)
        st.info("If an image result is not clear or incorrect, please go back to the 'Upload' tab to re-upload or retake the image, then click 'Start Extraction' again.")

# =========================
# Tab 3: Export
# =========================
with tab3:
    st.header("Export Data")
    
    if st.session_state['extraction_results'] is not None:
        df = st.session_state['extraction_results']
        
        st.write("Preview of data to be exported:")
        st.dataframe(df.head(), use_container_width=True)
        
        # Prepare file downloads
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        json_str = df.to_json(orient="records", indent=2)
        
        # Excel logic
        try:
            excel_bytes = to_excel(df)
            has_excel = True
        except ImportError:
            st.error("The 'openpyxl' library is missing. Please install it to enable Excel export.")
            has_excel = False
            excel_bytes = b""

        col1, col2, col3 = st.columns(3)
        with col1:
            if has_excel:
                st.download_button(
                    label="Download Excel",
                    data=excel_bytes,
                    file_name="namecards_extracted.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        with col2:
            st.download_button(
                label="Download CSV",
                data=csv_bytes,
                file_name="namecards_extracted.csv",
                mime="text/csv"
            )
        with col3:
            st.download_button(
                label="Download JSON",
                data=json_str,
                file_name="namecards_extracted.json",
                mime="application/json"
            )
            
    else:
        st.info("No data available. Please extract data in the 'Extract' tab first.")
