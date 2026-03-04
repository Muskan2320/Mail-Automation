# app_streamlit.py
import streamlit as st
import requests
import json
from pathlib import Path

# CONFIG
API_BASE = "http://127.0.0.1:8000"
GENERATE_ENDPOINT = f"{API_BASE}/generate-email"
SEND_ENDPOINT = f"{API_BASE}/send-email"

HISTORY_FILE = Path("sent_history.json")

# Helpers
def post_generate(jd_text: str, resume_bytes: bytes | None, resume_filename: str | None):
    files = {}
    data = {"jd_text": jd_text}
    if resume_bytes:
        files["resume_file"] = (resume_filename, resume_bytes, "application/pdf")

    resp = requests.post(GENERATE_ENDPOINT, data=data, files=files)
    return resp

def post_send(recipient: str, subject: str, body: str, jd_text: str, resume_bytes: bytes | None, resume_filename: str | None):
    data = {
        "recipient": recipient,
        "subject": subject,
        "body": body,
        "jd_text": jd_text,
    }

    files = {}
    if resume_bytes:
        files["resume_file"] = (resume_filename, resume_bytes, "application/pdf")

    resp = requests.post(SEND_ENDPOINT, data=data, files=files)
    return resp

def save_history(entry: dict):
    hist = []
    if HISTORY_FILE.exists():
        try:
            hist = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            hist = []
    hist.insert(0, entry)  # latest first
    HISTORY_FILE.write_text(json.dumps(hist[:200], indent=2), encoding="utf-8")  # keep last 200

# UI
st.set_page_config(page_title="AI Mail Assistant", layout="wide")
st.title("AI Job Application Email Assistant")

st.markdown("""
Enter the job description (JD) below, upload your PDF resume (optional), generate a personalized email using Gemini, preview/edit it, and send.
""")

with st.form("generate_form"):
    col1, col2 = st.columns([3,1])
    with col1:
        jd_text = st.text_area("Paste job description (JD)", height=300, placeholder="Paste the JD here...")
    with col2:
        st.markdown("**Resume (optional)**")
        resume_file = st.file_uploader("Upload PDF resume", type=["pdf"])
        st.markdown("---")
        # optional manual recipient override
        manual_recipient = st.text_input("Override recipient (optional)", "")
        st.write("You can optionally override the recipient suggested by AI.")
    submitted = st.form_submit_button("Generate Email")

if submitted:
    if not jd_text.strip():
        st.error("Please paste a Job Description before generating.")
    else:
        with st.spinner("Generating — calling AI..."):
            resume_bytes = None
            resume_name = None
            if resume_file is not None:
                resume_bytes = resume_file.getvalue()
                resume_name = resume_file.name

            try:
                resp = post_generate(jd_text, resume_bytes, resume_name)
            except Exception as e:
                st.error(f"Network error calling API: {e}")
                st.stop()

            if resp.status_code != 200:
                st.error(f"API returned {resp.status_code}: {resp.text}")
                st.stop()

            js = resp.json()
            if js.get("status") != "success":
                st.error(f"API error: {js}")
                st.stop()

            data = js.get("data", {})
            # Apply manual override if provided
            if manual_recipient.strip():
                data["recipient"] = manual_recipient.strip()

            # Show results in editable fields
            st.success("AI generated email fields. Edit if needed and click Send.")
            recipient = st.text_input("Recipient email", value=data.get("recipient",""))
            subject = st.text_input("Subject", value=data.get("subject",""))
            body = st.text_area("Body (editable)", value=data.get("body",""), height=300)

            # Provide Send button
            if st.button("Send Email"):
                if not (recipient and subject and body):
                    st.error("Recipient, Subject and Body are required to send.")
                else:
                    with st.spinner("Sending email..."):
                        try:
                            # We'll call send endpoint — it expects JD + optional resume.
                            send_resp = post_send(jd_text, resume_bytes, resume_name)
                        except Exception as e:
                            st.error(f"Network error during send: {e}")
                            st.stop()

                        if send_resp.status_code == 200:
                            st.success("Email sent! Response: " + send_resp.text)
                            # Save history
                            save_history({
                                "recipient": recipient,
                                "subject": subject,
                                "body": body,
                                "jd_excerpt": jd_text[:300],
                                "timestamp": st.time(),
                            })
                        else:
                            st.error(f"Send failed ({send_resp.status_code}): {send_resp.text}")

# History panel
st.sidebar.header("Recent Sends")
if HISTORY_FILE.exists():
    try:
        hist = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        hist = []
    for i, entry in enumerate(hist[:20]):
        st.sidebar.markdown(f"**{entry.get('subject')}**  \n{entry.get('recipient')}  \n{entry.get('timestamp')}")
else:
    st.sidebar.markdown("No history yet.")
