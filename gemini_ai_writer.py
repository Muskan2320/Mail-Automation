import os
import google.generativeai as genai
from dotenv import load_dotenv
import json

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def generate_mail_dict(jd_text, resume_text=None, resume_links=None):
    """
    Generates structured email data (recipient, subject, body)
    based on JD and optional resume.
    """

    prompt = f"""
    You are an intelligent assistant that writes professional emails.

    --- JOB DESCRIPTION ---
    {jd_text}

    --- RESUME ---
    {resume_text if resume_text else "Resume data not available. Use job description only."}
    --- RESUME LINKS ---
    {json.dumps(resume_links) if resume_links else "No links available."}

    --- TASK ---
    1. Identify recipient email from JD if present. If not present, return null.
    2. Create a short subject line either as per instructions in JD (if mentioned) or based on job title  (max 7 words).
    3. Write a short, professional, personalized body (4–6 lines), using resume if available.
    4. Do not use a template tone or cliché language.
    5. Output ONLY valid JSON in the following format:
    6. Ending of the mail should look like this:
       Looking forward to hearing from you

       Best Regards,
       Muskan Mulyan
       [Phone number]
       GitHub: [Github link] 
       LinkedIn:[Linkedin link]

    You will find phone number, github and linkedin links in the resume if provided. Don't mention if not available.

    {{
        "recipient": "email_or_null",
        "subject": "subject line here",
        "body": "mail body here"
    }}
    """

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)

    text = response.text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.replace("json", "", 1).strip()

    # Parse JSON safely
    try:
        data = json.loads(text)
        return data
    except Exception:
        return {"error": "Invalid AI JSON format", "raw": response.text}
