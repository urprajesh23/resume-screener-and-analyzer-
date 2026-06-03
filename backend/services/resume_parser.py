import docx
import PyPDF2
from PIL import Image
import io
import os
import google.generativeai as genai

def extract_text_from_pdf(file_bytes):
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    text = ''
    for page in pdf_reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted
    return text

def extract_text_from_docx(file_bytes):
    doc = docx.Document(io.BytesIO(file_bytes))
    text = ''
    for paragraph in doc.paragraphs:
        text += paragraph.text + '\n'
    return text

def extract_text_from_txt(file_bytes):
    try:
        return file_bytes.decode('utf-8')
    except UnicodeDecodeError:
        return file_bytes.decode('latin-1')

def extract_text_from_image(file_bytes):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        raise ValueError("Gemini API key is missing. Required for image processing.")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    img = Image.open(io.BytesIO(file_bytes))
    response = model.generate_content(["Extract all text from this resume image. Return ONLY the exact extracted text without any markdown or extra commentary.", img])
    return response.text

async def handle_file_upload(upload_file):
    filename = upload_file.filename.lower()
    file_bytes = await upload_file.read()
    
    if filename.endswith('.pdf'):
        return extract_text_from_pdf(file_bytes)
    elif filename.endswith('.docx'):
        return extract_text_from_docx(file_bytes)
    elif filename.endswith('.txt'):
        return extract_text_from_txt(file_bytes)
    elif filename.endswith(('.png', '.jpg', '.jpeg')):
        return extract_text_from_image(file_bytes)
    else:
        raise ValueError("Unsupported file type. Please upload PDF, DOCX, TXT, or Image.")
