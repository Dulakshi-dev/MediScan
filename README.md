---
title: MediScan
emoji: 🏥
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# MediRAG — AI Medical Report Analyzer

MediRAG helps patients understand their medical reports in plain English using RAG (Retrieval Augmented Generation).

## Live Demo
- **Frontend:** https://mediscan-iota-two.vercel.app
- **API Docs:** https://iddc-mediscan.hf.space/docs

## The Problem
When patients receive lab reports they see numbers with no context. Generic AI tools have no access to the patient's actual report and no guarantee their medical knowledge matches current clinical guidelines.

## The Solution
MediRAG combines two private knowledge sources using RAG:
1. The patient's uploaded report — extracted and parsed from PDF
2. A curated medical knowledge base — clinical reference ranges and guidelines

## Tech Stack
| Layer | Technology |
|---|---|
| Frontend | Next.js + Tailwind CSS |
| Backend | FastAPI (Python) |
| PDF Processing | PyMuPDF |
| RAG Pipeline | LangChain + ChromaDB |
| LLM | Groq API (Llama 3.1) |
| Database | Supabase (PostgreSQL) |
| Deploy | Vercel + HuggingFace Spaces |

## Features
- PDF upload and text extraction
- RAG-powered analysis grounded in medical knowledge base
- Normal / borderline / critical risk flagging
- Plain English explanations
- Doctor question suggestions
- Follow-up Q&A chat
- Report history

## Note
This tool is for educational purposes only. Always consult a qualified medical professional for health decisions.
