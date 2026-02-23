import io
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

def parse_pdf(file_stream: bytes) -> str:
    """
    Extracts text from a uploaded PDF file stream.
    """
    if PdfReader is None:
        return "[Error: pypdf is not installed. PDF parsing disabled.]"
        
    try:
        # Load the bytes into a readable buffer for PyPDF
        pdf_file = io.BytesIO(file_stream)
        
        # Read the file
        reader = PdfReader(pdf_file)
        
        extracted_text = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                extracted_text.append(f"\n--- Page {i + 1} ---\n{page_text}")
                
        return "\n".join(extracted_text)
    except Exception as e:
        return f"[Error parsing PDF: {str(e)}]"
