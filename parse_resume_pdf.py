import pdfplumber

def extract_text_from_pdf(pdf_path):
    """
    Extracts clean text from a PDF resume using pdfplumber.
    Works well for resumes (tables, bullets, formatting).
    """
    text = ""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"

    return text.strip()
