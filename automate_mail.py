import base64
import smtplib
from email.message import EmailMessage
import os
import mimetypes
from googleapiclient.errors import HttpError
from gmail_auth import get_gmail_service
from dotenv import load_dotenv

load_dotenv()

SENDER_EMAIL = os.getenv('sender_email')
SENDER_PASSWORD = os.getenv('sender_password')
MAX_ATTACHMENT_SIZE = 25 * 1024 * 1024

def send_mail_via_oauth(recipient_email, subject, body, attachment_path=None):
    try:
        service = get_gmail_service()

        if service is None:
            print("OAuth authentication failed — using SMTP fallback.")
            return False
        
        message = EmailMessage()
        message['To'] = recipient_email
        message['From'] = SENDER_EMAIL
        message['Subject'] = subject
        
        message.set_content(body, subtype="html")

        if attachment_path:
            print(f"Attachment path provided: {attachment_path}")
            if not os.path.exists(attachment_path):
                print("Attachment file does not exist at that path.")
            else:
                file_size = os.path.getsize(attachment_path)
                print(f"Attachment exists — size = {file_size} bytes")
                if file_size > MAX_ATTACHMENT_SIZE:
                    print("Attachment is larger than 25MB. Gmail may not attach this file directly.")
                    # you can either skip attaching or handle uploading to cloud here
                else:
                    ctype, encoding = mimetypes.guess_type(attachment_path)
                    if ctype is None:
                        ctype = 'application/octet-stream'
                    
                    maintype, subtype = ctype.split('/', 1)
                    with open(attachment_path, 'rb') as f:
                        file_data = f.read()
                        file_name = os.path.basename(attachment_path)
                    
                    message.add_attachment(file_data, maintype=maintype, subtype=subtype, filename=file_name)
                    print(f"Attached file: {file_name} (MIME: {maintype}/{subtype})")

        encodeed_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': encodeed_message}

        sent_message = service.users().messages().send(userId="me", body=create_message).execute()
        print(f"Email sent successfully! Message ID: {sent_message['id']}")

        return True
    except HttpError as error:
        print(f"Gmail API(OAuth) failed: {error}")
        return False
    except Exception as e:
        # Catch anything unexpected
        print(f"Unexpected error in OAuth mail sending: {e}")
        return False

# Fallback to SMTP if Gmail API fails
def send_mail_via_smtp(recipient_email, subject, body, attachment_path=None):
    msg = EmailMessage()
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg['Subject'] = subject
    
    msg.set_content(body, subtype="html")


    if attachment_path:
        print(f"Attachment path provided: {attachment_path}")
        if not os.path.exists(attachment_path):
            print("Attachment file does not exist at that path.")
        else:
            file_size = os.path.getsize(attachment_path)
            print(f"Attachment exists — size = {file_size} bytes")
            if file_size > MAX_ATTACHMENT_SIZE:
                print("Attachment is larger than 25MB. Gmail may not attach this file directly.")
                # you can either skip attaching or handle uploading to cloud here
            else:
                ctype, encoding = mimetypes.guess_type(attachment_path)
                if ctype is None:
                    ctype = 'application/octet-stream'
                maintype, subtype = ctype.split('/', 1)
                with open(attachment_path, 'rb') as f:
                    file_data = f.read()
                    file_name = os.path.basename(attachment_path)
                msg.add_attachment(file_data, maintype=maintype, subtype=subtype, filename=file_name)
                print(f"Attached file: {file_name} (MIME: {maintype}/{subtype})")

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
        
        print("Email sent successfully using SMTP fallback!")
        return True
    except Exception as e:
        print(f"SMTP fallback failed to send email: {e}")
        return False

def send_email(recipient_email, subject, body, attachment_path=None):
    print("Attempting to send email via Gmail API...")

    # First attempt: OAuth Gmail API
    success = send_mail_via_oauth(recipient_email, subject, body, attachment_path)

    if success:
        print("Email sent via Gmail API")
        return True

    # Fallback: SMTP
    print("OAuth failed — falling back to SMTP...")
    smtp_success = send_mail_via_smtp(recipient_email, subject, body, attachment_path)

    if smtp_success:
        print("Email sent via SMTP fallback")
        return True

    # Final failure
    print("Both OAuth and SMTP failed — email not sent.")
    return False

if __name__ == "__main__":
    send_email(
        recipient_email = "example@gmail.com",
        subject="Test Email with Attachment",
        body="Hello! This is a test email with an attachment sent from Python.",
        attachment_path="resume_muskan.pdf"
    )
