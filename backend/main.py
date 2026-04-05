from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pdf_extractor import process_medical_report
from analyzer import analyze_report
from rag_engine import retrieve_context
from pydantic import BaseModel

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

@app.get("/retrieve")
def retrieve(query: str):
    context = retrieve_context(query)
    return {"query": query, "context": context}

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    contents = await file.read()

    # Step 1: Extract text and values from PDF
    extracted = process_medical_report(contents)

    if not extracted["extracted_values"]:
        return {
            "error": "No medical values found in this PDF",
            "raw_text_preview": extracted["raw_text"][:300]
        }

    # Step 2: Analyze with RAG + Gemini
    analysis = analyze_report(extracted["extracted_values"])

    return {
        "file_name": file.filename,
        "analysis": analysis
    }

@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    contents = await file.read()
    result = process_medical_report(contents)
    return {
        "raw_text_preview": result["raw_text"][:500],
        "extracted_values": result["extracted_values"][:10],
        "total_values_found": len(result["extracted_values"])
    }

class QuestionRequest(BaseModel):
    question: str
    report_context: str

@app.post("/ask")
async def ask_question(request: QuestionRequest):
    from groq import Groq
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    medical_context = retrieve_context(request.question)

    prompt = f"""You are a medical assistant helping a patient understand their report.

Medical Knowledge:
{medical_context}

Patient's Report Context:
{request.report_context}

Patient's Question: {request.question}

Answer in plain English in 3-4 sentences. Always remind them to consult their doctor."""

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return {"answer": response.choices[0].message.content}