from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from supabase import create_client
from pdf_extractor import process_medical_report
from analyzer import analyze_report
from rag_engine import retrieve_context
from groq import Groq
from contextlib import asynccontextmanager
from rag_engine import load_knowledge_base

load_dotenv()
print("URL:", os.getenv("SUPABASE_URL"))
print("KEY:", os.getenv("SUPABASE_KEY")[:20] if os.getenv("SUPABASE_KEY") else "None")

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Building knowledge base on startup...")
    load_knowledge_base()
    print("Knowledge base ready!")
    yield

app = FastAPI(title="MediRAG API", lifespan=lifespan)

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

@app.get("/reports")
def get_reports():
    try:
        response = supabase.table("reports").select("*").order("created_at", desc=True).execute()
        return {"reports": response.data}
    except Exception as e:
        return {"reports": [], "error": str(e)}

@app.get("/reports/{report_id}")
def get_report(report_id: str):
    try:
        response = supabase.table("reports").select("*").eq("id", report_id).execute()
        if response.data:
            return {"report": response.data[0]}
        return {"error": "Report not found"}
    except Exception as e:
        return {"error": str(e)}

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    contents = await file.read()

    extracted = process_medical_report(contents)

    if not extracted["extracted_values"]:
        return {
            "error": "No medical values found in this PDF",
            "raw_text_preview": extracted["raw_text"][:300]
        }

    analysis = analyze_report(extracted["extracted_values"])

    # Save to Supabase
    try:
        supabase.table("reports").insert({
            "file_name": file.filename,
            "summary": analysis["summary"],
            "total_analyzed": analysis["total_analyzed"],
            "critical_count": analysis["critical_count"],
            "borderline_count": analysis["borderline_count"],
            "normal_count": analysis["normal_count"],
            "analyzed_values": analysis["analyzed_values"],
            "doctor_questions": analysis["doctor_questions"]
        }).execute()
    except Exception as e:
        print(f"Failed to save to database: {e}")

    return {
        "file_name": file.filename,
        "analysis": analysis
    }

class QuestionRequest(BaseModel):
    question: str
    report_context: str

@app.post("/ask")
async def ask_question(request: QuestionRequest):
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