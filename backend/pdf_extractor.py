import fitz
import re

MEDICAL_KEYWORDS = [
    "hemoglobin", "wbc", "rbc", "platelet", "glucose", "creatinine",
    "cholesterol", "alt", "ast", "tsh", "blood", "urine", "serum",
    "laboratory", "lab report", "pathology", "test results", "reference range",
    "normal range", "specimen", "patient"
]

KNOWN_TESTS = {
    # CBC
    "hemoglobin": "Hemoglobin",
    "rbc count": "RBC Count",
    "hematocrit": "Hematocrit",
    "mcv": "MCV",
    "mchc": "MCHC",
    "mch": "MCH",
    "rdw cv": "RDW",
    "rdw": "RDW",
    "wbc count": "WBC Count",
    "neutrophils": "Neutrophils",
    "lymphocytes": "Lymphocytes",
    "eosinophils": "Eosinophils",
    "monocytes": "Monocytes",
    "basophils": "Basophils",
    "platelet count": "Platelet Count",
    "mpv": "MPV",
    "esr": "ESR",
    # Blood sugar
    "fasting blood sugar": "Fasting Blood Sugar",
    "hba1c": "HbA1c",
    "mean blood glucose": "Mean Blood Glucose",
    # Lipids
    "cholesterol": "Cholesterol",
    "triglyceride": "Triglycerides",
    "hdl cholesterol": "HDL Cholesterol",
    "direct ldl": "Direct LDL",
    "vldl": "VLDL",
    "chol/hdl ratio": "CHOL/HDL Ratio",
    "ldl/hdl ratio": "LDL/HDL Ratio",
    # Thyroid
    "t3 - triiodothyronine": "T3",
    "t4 - thyroxine": "T4",
    "tsh - thyroid stimulating hormone": "TSH",
    # Urine
    "microalbumin": "Microalbumin",
    # Protein / Bilirubin
    "total protein": "Total Protein",
    "albumin": "Albumin",
    "globulin": "Globulin",
    "a/g ratio": "A/G Ratio",
    "total bilirubin": "Total Bilirubin",
    "conjugated bilirubin": "Conjugated Bilirubin",
    "unconjugated bilirubin": "Unconjugated Bilirubin",
    "delta bilirubin": "Delta Bilirubin",
    # Iron studies — longer keys before "iron"
    "total iron binding capacity": "TIBC",
    "transferrin saturation": "Transferrin Saturation",
    "iron": "Iron",
    # Biochemistry
    "homocysteine, serum": "Homocysteine",
    "creatinine, serum": "Creatinine",
    "blood urea nitrogen": "Blood Urea Nitrogen",
    "urea": "Urea",
    "uric acid": "Uric Acid",
    "calcium": "Calcium",
    "sgpt": "SGPT (ALT)",
    "sgot": "SGOT (AST)",
    # Electrolytes
    "sodium (na+)": "Sodium",
    "potassium (k+)": "Potassium",
    "chloride (cl-)": "Chloride",
    # Vitamins / Immunology
    "25(oh) vitamin d": "Vitamin D",
    "vitamin b12": "Vitamin B12",
    "psa-prostate specific antigen, total": "PSA",
    "ige": "IgE",
    # Haemoglobin electrophoresis — longer keys before "hb a"
    "hb a2": "Hb A2",
    "hb a": "Hb A",
    "foetal hb": "Foetal Hb",
}

# Matches a plain numeric value (no operator prefix).
# This is the ACTUAL result: "14.5", "189.0", "7.10", "10570"
PLAIN_NUMBER_RE = re.compile(
    r'^(\d{1,6}(?:[.,]\d{1,4})?)$'
)

# Matches operator-prefixed values like "< 148", ">100", "=190"
OPERATOR_NUMBER_RE = re.compile(
    r'^([<>=]\s*\d+\.?\d*)$'
)

# Standalone flag line — exactly "H" or "L" on its own line
STANDALONE_FLAG_RE = re.compile(r'^[HL]$', re.IGNORECASE)

UNIT_RE = re.compile(
    r'^(g/dL|g/L|mg/dL|mmol/L|µmol/L|umol/L|micromol/L|mEq/L|IU/L|U/L|'
    r'ng/mL|pg/mL|µg/dL|micro\s?g/dL|%|fL|pg|/cmm|/hpf|'
    r'million/cmm|thousand/cmm|mIU/mL|µIU/mL|microIU/mL|'
    r'mm/hr|mm/1hr|mg/L|nmol/L|pmol/L|IU/mL|S/Co)$',
    re.IGNORECASE
)

# Simple range like "13.0 - 16.5" or "74 - 106"
SIMPLE_RANGE_RE = re.compile(
    r'^\d+\.?\d*\s*[-–]\s*\d+\.?\d*$'
)

SKIP_FRAGMENTS = [
    "interpretation",
    "explanation",
    "reference :",
    "limitations",
    "increased in",
    "decreased in",
    "page ",
    "printed on",
    "approved on",
    "dr.",
    "m.d.",
    "md path",
    "hematopathologist",
    "pathology lab",
    "collected at",
    "collected on",
    "registration on",
    "sample type",
    "patient information",
    "sample information",
    "client name",
    "client/location",
    "location :",
    "process at",
    "end of report",
    "bio-rad",
    "biorad",
    "instrument name",
    "analysis comment",
    "calibrated",
    "peak name",
    "area %",
    "retention",
    "total area",
    "injection number",
    "run number",
    "rack id",
    "tube number",
    "operator id",
    "f concentration",
    "a2 concentration",
    "sterling accuris",
    "national reference",
    "jalaram",
    "website",
    "b/s.",
    "this is an electronically",
    "# referred",
    "scan qr",
    "passport no",
    "lab id",
    "ref. id",
    "ref. by",
    "sex/age",
    # Lipid-specific verbose range headers — these lines contain <> but are NOT values
    "desirable",
    "borderline",
    "optimal",
    "near to above",
    "very high",
    "normal :",
    "low:",
    "high:",
    "poor control",
    "good control",
    "for screening",
    "for diabetic",
    "pre-diabetes",
    "non-diabetes",
    "deficiency",
    "insufficiency",
    "sufficiency",
    "toxicity",
    "children :",
    "adult :",
    "non reactive",
    "reactive",
]


def extract_pages(pdf_bytes: bytes) -> list[str]:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = [page.get_text() for page in doc]
    doc.close()
    return pages


def is_medical_report(text: str) -> bool:
    tl = text.lower()
    return sum(1 for kw in MEDICAL_KEYWORDS if kw in tl) >= 3


def should_skip(line: str) -> bool:
    ll = line.lower()
    return any(frag in ll for frag in SKIP_FRAGMENTS)


def find_test(line: str):
    """Return (key, display_name) if line starts with a known test name."""
    ll = line.lower().strip()
    for key in sorted(KNOWN_TESTS, key=len, reverse=True):
        if ll == key or ll.startswith(key + " ") or ll.startswith(key + "\t"):
            return key, KNOWN_TESTS[key]
    return None, None


def normalize_value(value: str) -> str:
    """Strip leading zeros: '02' -> '2', keeps '<148' intact."""
    if PLAIN_NUMBER_RE.match(value.strip()):
        try:
            return str(float(value.replace(",", "")))
        except ValueError:
            pass
    return value


def extract_medical_values(pages: list[str]) -> list[dict]:
    results = []
    seen_keys = set()
    seen_display = set()

    for page_text in pages:
        lines = [ln.strip() for ln in page_text.splitlines() if ln.strip()]
        n = len(lines)
        i = 0

        while i < n:
            line = lines[i]

            if should_skip(line):
                i += 1
                continue

            key, display = find_test(line)
            if key is None or key in seen_keys or display in seen_display:
                i += 1
                continue

            # ── Collect candidates from the next WINDOW lines ──────────────
            # We scan up to 20 lines to handle verbose reference range pages.
            # We separately track:
            #   plain_value  — a bare number like "189.0" or "7.10"  (preferred)
            #   op_value     — an operator number like "<200"         (fallback only)
            #   flag         — H or L
            #   unit
            #   ref_range    — only simple "x - y" ranges stored here

            plain_value = None
            op_value = None
            flag = None
            unit = None
            ref_range = None

            # Check for standalone H/L on the very next non-empty line
            # (the PDF puts the flag on its own line right after the test name)
            j = i + 1
            if j < n and STANDALONE_FLAG_RE.match(lines[j].strip()):
                flag = lines[j].strip().upper()
                j_start = j + 1
            else:
                j_start = i + 1

            # Scan window
            for j in range(j_start, min(i + 21, n)):
                nl = lines[j].strip()

                if should_skip(nl):
                    continue

                # Stop at the next test name
                nk, _ = find_test(nl)
                if nk and nk != key:
                    break

                # Unit
                if UNIT_RE.match(nl) and unit is None:
                    unit = nl
                    continue

                # Simple reference range (store for display, don't confuse with value)
                if SIMPLE_RANGE_RE.match(nl) and ref_range is None:
                    ref_range = nl
                    continue

                # Plain number — this is the actual result we want
                if PLAIN_NUMBER_RE.match(nl) and plain_value is None:
                    plain_value = nl
                    continue

                # Multi-token line: look for plain number + optional unit
                tokens = nl.split()
                for ti, tok in enumerate(tokens):
                    # Standalone flag within a line e.g. "H 10570"
                    if STANDALONE_FLAG_RE.match(tok) and flag is None:
                        flag = tok.upper()
                        continue
                    if PLAIN_NUMBER_RE.match(tok) and plain_value is None:
                        plain_value = tok
                        for ut in tokens[ti + 1: ti + 3]:
                            if UNIT_RE.match(ut) and unit is None:
                                unit = ut
                        continue
                    if UNIT_RE.match(tok) and unit is None:
                        unit = tok
                    # Only store simple ranges, not verbose descriptions
                    if SIMPLE_RANGE_RE.match(tok) and ref_range is None:
                        ref_range = tok

            # Prefer plain number; fall back to operator number only if nothing else found
            final_value = plain_value if plain_value is not None else op_value

            if final_value is not None:
                seen_keys.add(key)
                seen_display.add(display)
                results.append({
                    "test_name": display,
                    "value": normalize_value(final_value),
                    "unit": unit or "N/A",
                    "reference_range": ref_range or "N/A",
                    "flag": "HIGH" if flag == "H" else ("LOW" if flag == "L" else None),
                })

            i += 1

    print(f"Extracted {len(results)} test values")
    return results


def process_medical_report(pdf_bytes: bytes) -> dict:
    pages = extract_pages(pdf_bytes)
    raw_text = "\n".join(pages)
    extracted_values = extract_medical_values(pages)
    return {
        "raw_text": raw_text,
        "extracted_values": extracted_values,
    }