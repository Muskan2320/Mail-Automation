from parse_resume_pdf import extract_text_from_pdf
from gemini_ai_writer import generate_mail_dict
from automate_mail import send_email

import os
import tempfile
import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI Job Application Email Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/generate-email")
async def generate_email_api(
    jd_text: str = Form(...),
    resume_file: UploadFile | None = File(None)
):
    try:
        resume_text, resume_links = None, None

        if resume_file:
            if resume_file.content_type != "application/pdf":
                raise HTTPException(status_code=400, detail="Only PDF resumes allowed.")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(await resume_file.read())
                resume_path = tmp.name

            resume_text, resume_links = extract_text_from_pdf(resume_path)
            os.remove(resume_path)

        email_data = generate_mail_dict(jd_text, resume_text, resume_links)

        if email_data.get("error"):
            raise HTTPException(status_code=500, detail="AI failed to generate email")

        return JSONResponse({
            "status": "success",
            "data": email_data
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during generation: {str(e)}"
        )

@app.post("/send-email")
async def send_email_api(
    recipient: str = Form(...),
    subject: str = Form(...),
    body: str = Form(...),
    cc: str | None = Form(None),
    resume_file: UploadFile | None = File(None)
):
    resume_path = None
    tmp_dir = None

    try:
        # Optional resume attachment
        if resume_file:
            if resume_file.content_type != "application/pdf":
                raise HTTPException(status_code=400, detail="Resume must be PDF")

            tmp_dir = tempfile.mkdtemp()
            resume_path = os.path.join(tmp_dir, resume_file.filename)

            with open(resume_path, "wb") as f:
                f.write(await resume_file.read())

        # Validate required fields
        if not all([recipient.strip(), subject.strip(), body.strip()]):
            raise HTTPException(
                status_code=400,
                detail="Recipient, subject, and body are required."
            )

        # CC handling (already comma-separated)
        cc_emails = None
        if cc and cc.strip():
            cc_emails = cc.strip()

        success = send_email(
            recipient_email=recipient,
            subject=subject,
            body=body,
            attachment_path=resume_path,
            cc_emails=cc_emails
        )

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Email sending failed via both OAuth and SMTP."
            )

        return {
            "status": "email_sent",
            "recipient": recipient,
            "cc": cc_emails,
            "subject": subject
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error while sending email: {str(e)}"
        )
    finally:
        if tmp_dir and os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)

@app.post("/regenerate-body")
async def regenerate_body_api(
    original_body: str = Form(...),
    instruction: str | None = Form(None),
    resume_file: UploadFile | None = File(None)
):
    resume_text = None

    try:
        if not original_body.strip():
            raise HTTPException(
                status_code=400,
                detail="Original email body is required to regenerate."
            )

        if resume_file:
            if resume_file.content_type != "application/pdf":
                raise HTTPException(status_code=400, detail="Resume must be PDF")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(await resume_file.read())
                resume_path = tmp.name

            resume_text, _ = extract_text_from_pdf(resume_path)
            os.remove(resume_path)

        final_instruction = (
            instruction.strip()
            if instruction and instruction.strip()
            else "Rewrite the email to be clearer and more concise while keeping the same intent."
        )

        new_body = regenerate_mail_body(
            original_body=original_body,
            instruction=final_instruction,
            resume_text=resume_text
        )

        return {
            "status": "success",
            "body": new_body
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to regenerate email body: {str(e)}"
        )
