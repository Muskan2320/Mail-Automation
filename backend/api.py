from parse_resume_pdf import extract_text_from_pdf
from gemini_ai_writer import generate_mail_dict, regenerate_mail_body
from automate_mail import send_email
from schemas import (
    SendEmailRequest,
    SendEmailResponse,
    GenerateEmailResponse,
    GenerateEmailData,
    RegenerateResponse,
    ErrorResponse
)

import os
import tempfile
import shutil
import logging
from pydantic import ValidationError

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# ---------- Setup ----------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Job Application Email Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["https://mail-automation-seven.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Global Error Handler ----------
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    error_code = exc.status_code
    message = exc.detail

    if not isinstance(message, str):
        message = str(message)

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_code=error_code,
            message=message
        ).dict()
    )


# ---------- Generate Email ----------
@app.post("/generate-email", response_model=GenerateEmailResponse)
async def generate_email_api(
    jd_text: str = Form(...),
    resume_file: UploadFile | None = File(None)
):
    try:
        resume_text, resume_links = None, None

        if resume_file:
            if resume_file.content_type != "application/pdf":
                raise HTTPException(
                    status_code=400,
                    detail={"code": "INVALID_FILE", "message": "Resume must be PDF"}
                )

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(await resume_file.read())
                resume_path = tmp.name

            resume_text, resume_links = extract_text_from_pdf(resume_path)
            os.remove(resume_path)

        email_data = generate_mail_dict(jd_text, resume_text, resume_links)

        if email_data.get("error"):
            raise HTTPException(
                status_code=500,
                detail={"code": "AI_GENERATION_FAILED", "message": "AI failed to generate email"}
            )

        logger.info(f"Generated email data: {email_data}")

        return GenerateEmailResponse(
            status="success",
            data=GenerateEmailData(**email_data)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_ERROR", "message": f"Unexpected error during generation: {str(e)}"}
        )


# ---------- Send Email ----------
@app.post("/send-email", response_model=SendEmailResponse)
async def send_email_api(
    recipient: str = Form(...),
    subject: str = Form(...),
    body: str = Form(...),
    cc: str | None = Form(None),
    resume_file: UploadFile | None = File(None)
):
    logger.info(f"Sending email to: {recipient}, cc: {cc}")
    print("ENTERED")
    resume_path = None
    tmp_dir = None

    try:
        if not all([recipient, subject.strip(), body.strip()]):
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "EMPTY_FIELDS",
                    "message": "Recipient, subject, and body are required."
                }
            )

        # Convert recipient → list
        recipient_list = [
            email.strip()
            for email in recipient.split(",")
            if email.strip() and "@" in email
        ]

        # Convert cc → list (future-proof)
        cc_list = None
        if cc and cc.strip():
            cc_list = [
                email.strip()
                for email in cc.split(",")
                if email.strip() and "@" in email
            ]

            if not cc_list:
                cc_list = None

        data = SendEmailRequest(
            recipient=recipient_list,
            subject=subject,
            body=body,
            cc=cc_list
        )

        # Convert to string for SMTP
        recipient_str = ",".join(data.recipient)
        cc_emails = ",".join(data.cc) if data.cc else None

        if resume_file:
            if resume_file.content_type != "application/pdf":
                raise HTTPException(
                    status_code=400,
                    detail={
                        "code": "INVALID_FILE",
                        "message": "Resume must be PDF"
                    }
                )

            tmp_dir = tempfile.mkdtemp()
            resume_path = os.path.join(tmp_dir, resume_file.filename)

            with open(resume_path, "wb") as f:
                f.write(await resume_file.read())

        success = send_email(
            recipient_email=recipient_str,
            subject=subject,
            body=body,
            attachment_path=resume_path,
            cc_emails=cc_emails
        )

        success = True
        if not success:
            raise HTTPException(
                status_code=500,
                detail={
                    "code": "EMAIL_SEND_FAILED",
                    "message": "Email sending failed"
                }
            )
        
        return SendEmailResponse(
            status="success",
            recipient=data.recipient,       
            cc=data.cc,                 
            subject=subject
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "VALIDATION_ERROR",
                "message": e.errors()
            }
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_ERROR",
                "message": f"Unexpected error while sending email: {str(e)}"
            }
        )

    finally:
        if tmp_dir and os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)

# ---------- Regenerate Email ----------
@app.post("/regenerate-body", response_model=RegenerateResponse)
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
                detail={"code": "BODY_MISSING", "message": "Original email body is required"}
            )

        if resume_file:
            if resume_file.content_type != "application/pdf":
                raise HTTPException(
                    status_code=400,
                    detail={"code": "INVALID_FILE", "message": "Resume must be PDF"}
                )

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

        return RegenerateResponse(
            status="success",
            body=new_body
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_ERROR", "message": f"Failed to regenerate email: {str(e)}"}
        )
