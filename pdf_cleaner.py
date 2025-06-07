import os
import re
import fitz  # PyMuPDF

# Paths
PDF_FOLDER = "./dataset/research_papers/"
CLEANED_FOLDER = "./dataset/cleaned_papers/"

def clean_text(text):
    """Cleans extracted text by removing references, links, and unnecessary sections"""
    text = re.sub(r"http[s]?://\S+", "", text)  # Remove URLs
    text = re.sub(r"\[[0-9]+\]", "", text)      # Remove reference numbers like [1]
    return text

def extract_text_pymupdf(pdf_path):
    """Extract text from PDF using PyMuPDF (block-sorted for column awareness)"""
    doc = fitz.open(pdf_path)
    all_text = ""

    for page in doc:
        blocks = page.get_text("blocks")  # returns: (x0, y0, x1, y1, "text", block_no, ...)
        sorted_blocks = sorted(blocks, key=lambda b: (b[1], b[0]))  # sort by Y, then X
        for block in sorted_blocks:
            text = block[4].strip()
            if text:
                all_text += text + "\n"
    
    return all_text

def extract_and_clean_pdf(pdf_path, output_path):
    """Extracts and cleans text from a PDF using PyMuPDF"""
    try:
        raw_text = extract_text_pymupdf(pdf_path)
        cleaned_text = clean_text(raw_text)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(cleaned_text)

        print(f"✅ Cleaned text saved to {output_path}")
    
    except Exception as e:
        print(f"⚠️ Error processing {pdf_path}: {e}")

def process_all_pdfs(pdf_folder, cleaned_folder):
    """Processes all PDFs in the research papers folder"""
    if not os.path.exists(cleaned_folder):
        os.makedirs(cleaned_folder)
    
    pdf_files = [f for f in os.listdir(pdf_folder) if f.endswith(".pdf")]
    if not pdf_files:
        print("❌ No PDFs found in the folder.")
        return
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_folder, pdf_file)
        cleaned_text_path = os.path.join(cleaned_folder, f"{os.path.splitext(pdf_file)[0]}.txt")
        extract_and_clean_pdf(pdf_path, cleaned_text_path)

if __name__ == "__main__":
    process_all_pdfs(PDF_FOLDER, CLEANED_FOLDER)
