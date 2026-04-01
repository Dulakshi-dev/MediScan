import fitz
import re

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    doc.close()
    return full_text

def extract_medical_values(text: str) -> list:
    values = []
    
    # Pattern to match: Test Name followed by value and unit
    # Covers patterns like "Hemoglobin 13.2 g/dL" or "Glucose: 5.8 mmol/L"
    pattern = r'([A-Za-z\s\(\)]+)[\s:]+(\d+\.?\d*)\s*([a-zA-Z/%µ]+(?:/[a-zA-Z]+)?)'
    
    matches = re.findall(pattern, text)
    
    for match in matches:
        name = match[0].strip()
        value = match[1].strip()
        unit = match[2].strip()
        
        # Filter out very short names (likely false positives)
        if len(name) > 3:
            values.append({
                "test_name": name,
                "value": value,
                "unit": unit
            })
    
    return values

def process_medical_report(pdf_bytes: bytes) -> dict:
    raw_text = extract_text_from_pdf(pdf_bytes)
    extracted_values = extract_medical_values(raw_text)
    
    return {
        "raw_text": raw_text,
        "extracted_values": extracted_values
    }