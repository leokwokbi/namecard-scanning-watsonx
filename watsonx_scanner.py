import os
import io
import json
import base64
import pandas as pd
import streamlit as st
from PIL import Image

from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams


st.set_page_config(page_title="Watsonx Namecard Scanner", page_icon="📇", layout="wide")

st.title("Watsonx.ai Batch Namecard Scanner")
st.write("Batch upload business card images and extract structured contact data with a vision model.")


# -------------------------
# Sidebar: watsonx settings
# -------------------------
st.sidebar.header("Watsonx.ai Settings")

# Allow defaults via environment variables for convenience in server deployments
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

st.sidebar.caption("Tip: Keep the API Key secret. Prefer Streamlit Secrets or environment variables in production.")


# -------------------------
# Helpers
# -------------------------
def file_to_base64(uploaded_file) -> str:
    return base64.b64encode(uploaded_file.getvalue()).decode("utf-8")


def detect_mime(filename: str) -> str:
    ext = (filename.split(".")[-1] or "").lower()
    if ext in ("jpg", "jpeg"):
        return "image/jpeg"
    if ext == "png":
        return "image/png"
    if ext == "bmp":
        return "image/bmp"
    # Fallback: most vision endpoints accept jpeg; caller can convert if needed
    return "image/jpeg"


def extract_namecard_json(image_b64: str, mime_type: str) -> dict:
    """
    Sends an image to a watsonx.ai vision-capable chat model and returns a parsed JSON dict.
    """
    credentials = {"url": url, "apikey": api_key}

    prompt_text = (
        "You are given a business card image.\n"
        "Extract information and return STRICT JSON ONLY, with exactly these keys:\n"
        '{\n'
        '  "Name": string|null,\n'
        '  "Title": string|null,\n'
        '  "Company": string|null,\n'
        '  "Phone": string|null,\n'
        '  "Email": string|null,\n'
        '  "Website": string|null,\n'
        '  "Address": string|null\n'
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

    # Defensive cleanup if the model ever wraps JSON
    cleaned = content.replace("```json", "").replace("```", "").strip()

    return json.loads(cleaned)


# -------------------------
# UI: batch upload
# -------------------------
uploaded_files = st.file_uploader(
    "Upload business card images (batch supported)",
    type=["png", "jpg", "jpeg", "bmp"],
    accept_multiple_files=True,
)

colA, colB = st.columns([1, 1], vertical_alignment="top")

with colA:
    st.subheader("Inputs")
    st.write("1) Enter watsonx settings in the sidebar.")
    st.write("2) Upload multiple images.")
    st.write("3) Click Start Batch Processing.")

with colB:
    st.subheader("Output")
    st.write("Results will appear as a table, and you can download CSV/JSON.")


can_run = bool(api_key and project_id and url and uploaded_files)

start = st.button("Start Batch Processing", type="primary", disabled=not can_run)

if uploaded_files and not (api_key and project_id and url):
    st.warning("Please enter API Key, Project ID, and Service URL in the sidebar before processing.")

if start:
    results = []
    progress = st.progress(0.0)
    status = st.empty()

    for idx, f in enumerate(uploaded_files, start=1):
        status.write(f"Processing: {f.name} ({idx}/{len(uploaded_files)})")

        try:
            b64 = file_to_base64(f)
            mime = detect_mime(f.name)
            data = extract_namecard_json(b64, mime)

            row = {"File Name": f.name, **data, "Error": None}
        except Exception as e:
            row = {"File Name": f.name, "Name": None, "Title": None, "Company": None,
                   "Phone": None, "Email": None, "Website": None, "Address": None,
                   "Error": str(e)}

        results.append(row)
        progress.progress(idx / len(uploaded_files))

    progress.empty()
    status.success("Done.")

    df = pd.DataFrame(results)

    st.subheader("Extracted Data")
    st.dataframe(df, use_container_width=True)

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    json_str = df.to_json(orient="records", indent=2)

    d1, d2 = st.columns(2)
    with d1:
        st.download_button("Download CSV", data=csv_bytes, file_name="namecards.csv", mime="text/csv")
    with d2:
        st.download_button("Download JSON", data=json_str, file_name="namecards.json", mime="application/json")

    with st.expander("Preview uploaded images"):
        cols = st.columns(3)
        for i, f in enumerate(uploaded_files):
            img = Image.open(io.BytesIO(f.getvalue()))
            cols[i % 3].image(img, caption=f.name, width=280)
