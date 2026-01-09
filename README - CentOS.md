<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Convert the readme file from using ubuntu os to centos

Here is the converted **README.md** file tailored for a **CentOS** (or RHEL-based) environment.

The key changes include:

1. **Package Management**: Replaced `apt` commands with `dnf` (the standard for CentOS 8/Stream 9).
2. **Prerequisites**: Updated OS recommendations to CentOS Stream/RHEL.
3. **ngrok Installation**: Switched from `apt` (which isn't native to CentOS) to the universal **binary installation** method, which is cleaner than setting up Snap/EPEL repositories on CentOS just for one tool.

***

# 📇 Watsonx.ai Batch Namecard Scanner (CentOS Deployment)

A professional Streamlit web application that uses **IBM watsonx.ai** generative AI (Vision Models) to extract structured contact information from business card images.

## 🌟 Features

* **Batch Processing**: Upload multiple namecards at once.
* **AI-Powered Extraction**: Uses `llama-3-2-11b-vision-instruct` (or similar) to understand image content without regex.
* **Structured Output**: Automatically extracts Name, Title, Company, Phone, Email, Website, and Address into JSON format.
* **Export Options**: Download results as CSV or JSON files.
* **Public Access**: Includes instructions for exposing the local server via **ngrok**.

***

## 📋 Prerequisites

Before you begin, ensure you have:

1. **CentOS Stream 9** or **RHEL 8/9**.
2. **Root or Sudo access**.
3. An **IBM Cloud Account** with access to **watsonx.ai** credentials (API Key, Project ID, Service URL).

***

## 🚀 End-to-End Setup Guide

### Step 1: Update System \& Install Git/Python

Open your terminal and run the following commands to update package lists and install necessary tools.

```bash
sudo dnf update -y
sudo dnf install -y python3 python3-pip git
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

Since CentOS does not have a native `apt` repository for ngrok, we will install the binary directly.[^1][^2]

**1. Install ngrok**

```bash
# Download the latest Linux binary
curl -O https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz

# Unzip to /usr/local/bin (requires sudo)
sudo tar xvzf ngrok-v3-stable-linux-amd64.tgz -C /usr/local/bin
```

**2. Configure Auth Token**
(Sign up at [dashboard.ngrok.com](https://dashboard.ngrok.com) to get your free token)

```bash
ngrok config add-authtoken <YOUR_AUTH_TOKEN>
```

**3. Start ngrok Tunnel**
Start a screen session or background process to keep ngrok running:

```bash
nohup ngrok http 8501 > ngrok.log 2>&1 &
```

* Copy the **Forwarding URL** (e.g., `https://a1b2-c3d4.ngrok-free.app`) from the log file or dashboard.
* If you need to check the URL from the terminal: `grep "url=" ngrok.log`

***

## 📖 User Guide

1. **Access the App**: Open the ngrok URL in your browser.
2. **Enter Credentials**: On the left sidebar, paste your **IBM Cloud API Key**, **Project ID**, and **Service URL**.
3. **Upload \& Scan**: Upload your namecard images and click **Start Batch Processing**.
4. **Download Data**: Export your results as CSV or JSON.

***

## 🔧 Maintenance Commands

* **Stop the App**:

```bash
pkill -f streamlit
pkill -f ngrok
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

<span style="display:none">[^10][^11][^12][^13][^14][^15][^16][^3][^4][^5][^6][^7][^8][^9]</span>

<div align="center">⁂</div>

[^1]: https://ngrok.com/docs/guides/device-gateway/linux

[^2]: https://ngrok.mintlify.dev/docs/guides/device-gateway/linux

[^3]: README.md

[^4]: https://ngrok.com/download

[^5]: https://snapcraft.io/install/ngrok/centos

[^6]: https://snapcraft.io/install/ngrok/rhel

[^7]: https://gist.github.com/41a662dbaa24f98a43becf489143b86f

[^8]: https://gist.github.com/SalahHamza/799cac56b8c2cd20e6bfeb8886f18455

[^9]: https://www.geeksforgeeks.org/installation-guide/how-to-install-ngrok-on-linux/

[^10]: https://www.youtube.com/watch?v=MA7cxy41N8Y

[^11]: https://learn.arm.com/learning-paths/servers-and-cloud-computing/gh-copilot-simple/run-ngrok/

[^12]: https://github.com/CPScript/Ngrok

[^13]: https://serverspace.io/support/help/ngrok-installation-and-traffic-policies/

[^14]: https://ngrok.com/docs/getting-started

[^15]: https://linuxhint.com/set-up-use-ngrok/

[^16]: https://blog.csdn.net/sumengnan/article/details/125016761

