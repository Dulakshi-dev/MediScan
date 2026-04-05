import fitz
import re

KNOWN_TESTS = [
    "Hemoglobin", "RBC Count", "Hematocrit", "MCV", "MCH", "MCHC",
    "RDW", "WBC Count", "Neutrophils", "Lymphocytes", "Eosinophils",
    "Monocytes", "Basophils", "Platelet Count", "Glucose", "Creatinine",
    "Urea", "Sodium", "Potassium", "Chloride", "Calcium", "Albumin",
    "Total Protein", "Bilirubin", "ALT", "AST", "ALP", "GGT",
    "Cholesterol", "Triglycerides", "HDL", "LDL", "TSH", "T3", "T4",
    "HbA1c", "ESR", "CRP", "Uric Acid", "Iron", "Ferritin",
    "Vitamin D", "Vitamin B12", "Folate", "PSA", "AFP",
    "Total WBC", "Differential Count"
]

METHODS = [
    "Colorimetric", "Electrical impedance", "Calculated", "Derived",
    "Microscopic", "Nephelometry", "ELISA", "Immunoturbidimetry",
    "SF Cube cell analysis", "Electrochemiluminescence", "Flow cytometry"
]

UNITS = [
    "g/dL", "g/L", "mg/dL", "mmol/L", "µmol/L", "umol/L",
    "mEq/L", "IU/L", "U/L", "ng/mL", "pg/mL", "µg/dL",
    "%", "fL", "pg", "/cmm", "million/cmm", "thousand/cmm",
    "mIU/mL", "µIU/mL", "mm/hr", "mg/L", "nmol/L", "pmol/L"
]

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    doc.close()
    return full_text

def is_numeric(value: str) -> bool:
    try:
        float(value.replace(",", ""))
        return True
    except ValueError:
        return False

def is_method(line: str) -> bool:
    return any(method.lower() in line.lower() for method in METHODS)

def is_unit(line: str) -> bool:
    return any(unit.lower() == line.strip().lower() for unit in UNITS)

def is_reference_range(line: str) -> bool:
    return bool(re.match(r'^\d+\.?\d*\s*[-–]\s*\d+\.?\d*$', line.strip()))

def find_test_name(line: str) -> str | None:
    line_clean = line.strip()
    for test in KNOWN_TESTS:
        if test.lower() in line_clean.lower():
            return test
    return None

def extract_medical_values(text: str) -> list:
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    results = []
    i = 0

    while i < len(lines):
        test_name = find_test_name(lines[i])

        if test_name:
            unit = None
            reference_range = None
            value = None

            # Look ahead up to 6 lines for unit, range, method, value
            j = i + 1
            while j < min(i + 7, len(lines)):
                line = lines[j].strip()

                if is_unit(line) and unit is None:
                    unit = line

                elif is_reference_range(line) and reference_range is None:
                    reference_range = line

                elif is_method(line):
                    pass  # skip method lines

                elif is_numeric(line) and value is None:
                    # Make sure it's not a reference range value
                    if reference_range is None or line not in reference_range:
                        value = line

                j += 1

            if value is not None:
                # Determine if flagged (H or L on same line as value)
                flag = None
                value_line = value
                if value.endswith(" H") or value.endswith("\tH"):
                    flag = "HIGH"
                    value = value.replace(" H", "").replace("\tH", "").strip()
                elif value.endswith(" L") or value.endswith("\tL"):
                    flag = "LOW"
                    value = value.replace(" L", "").replace("\tL", "").strip()

                results.append({
                    "test_name": test_name,
                    "value": value,
                    "unit": unit or "N/A",
                    "reference_range": reference_range or "N/A",
                    "flag": flag
                })

        i += 1

    return results

def process_medical_report(pdf_bytes: bytes) -> dict:
    raw_text = extract_text_from_pdf(pdf_bytes)
    extracted_values = extract_medical_values(raw_text)

    return {
        "raw_text": raw_text,
        "extracted_values": extracted_values
    }