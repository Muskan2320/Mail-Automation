import pdfplumber
from urllib.parse import urlparse

def friendly_text_from_url(url):
    url = url.lower()
    
    if url.startswith("mailto:"):
        return "Email"
    if url.startswith("tel:"):
        return "Phone"
    if "github.com" in url:
        return "GitHub"
    if "linkedin.com" in url:
        return "LinkedIn"

    # For company websites → extract domain name
    try:
        domain = urlparse(url).netloc.replace("www.", "")
        name = domain.split(".")[0]
        return name.capitalize()
    except:
        return None


def extract_text_from_pdf(pdf_path):
    full_text = ""
    links = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            full_text += (page.extract_text() or "") + "\n"

            if page.annots:
                for annot in page.annots:
                    url = annot.get("uri")
                    if not url and isinstance(annot.get("A"), dict):
                        url = annot["A"].get("URI")
                    if not url:
                        continue

                    # Auto-generate meaningful text
                    text = friendly_text_from_url(url)

                    links.append({
                        "url": url,
                        "text": text
                    })

    return full_text.strip(), links
