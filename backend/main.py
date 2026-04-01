from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import UploadFile, File
from pdf_extractor import process_medical_report

app = FastAPI(title="MediRAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "MediRAG API is running"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    contents = await file.read()
    result = process_medical_report(contents)
    return {
        "raw_text_preview": result["raw_text"][:500],
        "extracted_values": result["extracted_values"][:10],
        "total_values_found": len(result["extracted_values"])
    }