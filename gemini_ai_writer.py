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
    1. Identify recipient email from JD if present. If not present, return null. If more than one email is present, write them comma separated.
    2. Identify CC email from JD if present. If not present, return null. If more than one email is present, write them comma separated.
    3. Create a short subject line either as per instructions in JD (if mentioned) or based on job title  (max 7 words).
    4. Write a short, professional, personalized body (2–5 lines i.e. not more than a paragraph), using resume if available.
    5. Do not use a template tone or cliché language.
    6. Output ONLY valid JSON in the following format:
    7. Ending of the mail should look like this (keep it compact with NO space between lines):
       Best Regards,
       Muskan Mulyan
       [Phone number]
       GitHub: [Github link] 
       LinkedIn:[Linkedin link]

    You will find phone number, github and linkedin links in the resume if provided. Don't mention if not available. Returns lines immediately one after another without empty lines in between for the signature.

    {{
        "recipient": "email_or_null",
        "cc": "cc_email_or_null",
        "subject": "subject line here",
        "body": "mail body here"
    }}

    NOTE: Maintain the format, spacing, line change and data you are generating is inserted into the text editor, so if require highlight the important text also.
    """

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)

    text = response.text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.replace("json", "", 1).strip()

    try:
        data = json.loads(text)
        
        if "body" in data and data["body"]:
            data["body"] = data["body"].replace("\n", "<br>")
        return data
    except Exception:
        return {"error": "Invalid AI JSON format", "raw": response.text}

def regenerate_mail_body(original_body: str, instructions: str | None = Form(None), resume_text: str | None = None):
    """
    Regenerates ONLY the email body based on a user instruction.
    """
    
    final_instruction = (
        instruction.strip()
        if instruction and instruction.strip()
        else "Rewrite the email to be clearer and more concise while keeping the same intent."
    )

    prompt = f"""
    You are an intelligent assistant helping refine professional emails.

    --- ORIGINAL EMAIL BODY ---
    {original_body}

    --- USER INSTRUCTION ---
    {final_instruction}

    --- RESUME CONTEXT ---
    {resume_text if resume_text else "Resume not available."}

    --- TASK ---
    Rewrite ONLY the email body based on the instruction.
    Keep it professional and concise.
    Do NOT add subject or recipient.
    Return ONLY the rewritten body as plain text.
    """

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)

    return response.text.strip()