from parse_resume_pdf import extract_text_from_pdf
from gemini_ai_writer import generate_mail_dict
from automate_mail import send_email

import os
import tempfile
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI(title="AI Job Application Email Generator API")

@app.post("/generate-email")
async def generate_email_api(
    jd_text: str = Form(...),
    resume_file: UploadFile | None = File(None)
):
    resume_text, resume_links = None, None

    if resume_file:
        if resume_file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Only PDF resumes allowed.")

        # Save temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(await resume_file.read())
            resume_path = tmp.name

        resume_text, resume_links = extract_text_from_pdf(resume_path)
        os.remove(resume_path)

    email_data = generate_mail_dict(jd_text, resume_text, resume_links)
    
    return JSONResponse({"status": "success", "data": email_data})


@app.post("/send-email")
async def send_email_api(
    jd_text: str = Form(...),
    resume_file: UploadFile | None = File(None)
):
    resume_text = None
    resume_path = None

    # Handle optional resume
    if resume_file:
        if resume_file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Resume must be PDF")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(await resume_file.read())
            resume_path = tmp.name
            resume_text, resume_links = extract_text_from_pdf(tmp.name)

    # AI Extracted email fields
    email_data = generate_mail_dict(jd_text, resume_text, resume_links)
    
    if email_data.get("error"):
        raise HTTPException(status_code=500, detail="AI failed to return valid email fields")

    recipient = email_data.get("recipient")
    subject = email_data.get("subject")
    body = email_data.get("body")

    if not all([recipient, subject, body]):
        return JSONResponse({
            "status": "incomplete_fields",
            "message": "Email not sent — Missing required values",
            "data": email_data
        })

    # Send the email
    send_email(
        recipient_email=recipient,
        subject=subject,
        body=body,
        attachment_path=resume_path
    )

    if resume_path: os.remove(resume_path)

    return {
        "status": "email_sent",
        "recipient": recipient,
        "subject": subject
    }