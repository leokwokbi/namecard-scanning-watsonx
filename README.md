# 📇 Watsonx.ai Batch Namecard Scanner (Ubuntu Deployment)

A professional Streamlit web application that uses **IBM watsonx.ai** generative AI (Vision Models) to extract structured contact information from business card images.

## 🌟 Features
*   **Batch Processing**: Upload multiple namecards at once.
*   **AI-Powered Extraction**: Uses `llama-3-2-11b-vision-instruct` (or similar) to understand image content without regex.
*   **Structured Output**: Automatically extracts Name, Title, Company, Phone, Email, Website, and Address into JSON format.
*   **Export Options**: Download results as CSV or JSON files.
*   **Public Access**: Includes instructions for exposing the local server via **ngrok**.

---

## 📋 Prerequisites

Before you begin, ensure you have:
1.  **Ubuntu Server** (20.04 or 22.04 LTS recommended).
2.  **Root or Sudo access**.
3.  An **IBM Cloud Account** with access to **watsonx.ai** credentials (API Key, Project ID, Service URL).

---

## 🚀 End-to-End Setup Guide

### Step 1: Update System & Install Git/Python
Open your terminal and run the following commands to update package lists and install necessary tools.
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git
```


### Step 2: Clone the Repository

Download the project files directly from GitHub.

```bash
cd ~
git clone https://github.com/leokwokbi/namecard-scanning-watsonx.git
cd namecard-scanning-watsonx
```


### Step 3: Create Virtual Environment

Isolate your project dependencies.

```bash
python3 -m venv venv
source venv/bin/activate
```

*(You will see `(venv)` appear at the start of your command prompt)*

### Step 4: Install Dependencies

Install the required Python libraries listed in `requirements.txt`.

```bash
pip install -r requirements.txt
```


### Step 5: Run the Application (Background Mode)

To keep the app running even if you close the terminal, use `nohup`.

```bash
nohup streamlit run watsonx_scanner.py --server.port 8501 --server.address 0.0.0.0 > streamlit.log 2>&1 &
```

* The app is now running in the background on port 8501.
* You can check logs with: `tail -f streamlit.log`


### Step 6: Expose to Public Internet with ngrok

**1. Install ngrok**

```bash
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok
```

**2. Configure Auth Token**
(Sign up at [dashboard.ngrok.com](https://dashboard.ngrok.com) to get your free token)

```bash
ngrok config add-authtoken <YOUR_AUTH_TOKEN>
```

**3. Start ngrok Tunnel**
Start a screen session to keep ngrok running:

```bash
sudo apt install screen -y
screen -S ngrok_session
ngrok http 8501
```

* Copy the **Forwarding URL** (e.g., `https://a1b2-c3d4.ngrok-free.app`).
* Press `Ctrl+A`, then `D` to detach the screen (ngrok keeps running).

---

## 📖 User Guide

1. **Access the App**: Open the ngrok URL in your browser.
2. **Enter Credentials**: On the left sidebar, paste your **IBM Cloud API Key**, **Project ID**, and **Service URL**.
3. **Upload \& Scan**: Upload your namecard images and click **Start Batch Processing**.
4. **Download Data**: Export your results as CSV or JSON.

---

## 🔧 Maintenance Commands

* **Stop the App**:

```bash
pkill -f streamlit
```

* **Update the App (Pull latest changes)**:

```bash
cd ~/namecard-scanning-watsonx
git pull
```

* **View App Logs**:

```bash
tail -f ~/namecard-scanning-watsonx/streamlit.log
```


```
<span style="display:none">[^1]</span>

<div align="center">⁂</div>

[^1]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/149253418/2e23b7a3-73ad-41d4-9140-96410ee531ac/Qwen_python_20260105_ziohd7q68.py```

