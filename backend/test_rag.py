# test_extract.py - run with: python test_extract.py
import fitz

doc = fitz.open("sterling-accuris-pathology-sample-report-unlocked.pdf")
for i, page in enumerate(doc):
    if i in [2, 3, 4, 11]:  # lipid, FBS, HbA1c, vitamin pages
        print(f"\n=== PAGE {i+1} ===")
        print(page.get_text())