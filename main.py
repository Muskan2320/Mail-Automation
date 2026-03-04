from parse_resume_pdf import extract_text_from_pdf
from gemini_ai_writer import generate_mail_dict
from automate_mail import send_email

if __name__ == "__main__":
    jd_text = open("jd.txt", "r").read()

    # Extract resume text from PDF
    resume_text, resume_links = extract_text_from_pdf("resume_muskan.pdf")

    # Generate email body using Gemini
    email_dict = generate_mail_dict(jd_text, resume_text, resume_links)

    print("=== GENERATED MAIL ===")
    print(email_dict['body'])

    # Send mail with the same PDF attached
    send_email(
        recipient_email="recruiter@example.com",
        subject="Application for the AI Position",
        body=email_dict['body'],
        attachment_path="resume_muskan.pdf",
    )
