import os
import json
from groq import Groq
from rag_engine import retrieve_context
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.1-8b-instant"

def analyze_all_values(extracted_values: list) -> list:
    test_names = ", ".join([v["test_name"] for v in extracted_values[:15]])
    context = retrieve_context(f"Normal ranges and clinical significance of {test_names}")

    values_text = "\n".join([
        f"- {v['test_name']}: {v['value']} {v['unit']} (reference: {v.get('reference_range', 'N/A')})"
        for v in extracted_values[:15]
    ])

    prompt = f"""You are a medical report analyzer. Analyze these lab results and respond ONLY with a valid JSON array. No explanation, no markdown, just the JSON array.

Medical Knowledge Context:
{context}

Lab Results:
{values_text}

Respond with exactly this JSON array, one object per test:
[
  {{
    "test_name": "test name",
    "value": "value",
    "unit": "unit",
    "reference_range": "range or N/A",
    "status": "normal or borderline or critical",
    "explanation": "plain English explanation in 2 sentences",
    "concern_level": "none or low or medium or high",
    "doctor_question": "one specific question to ask doctor"
  }}
]

Return ONLY the JSON array. No other text."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )

    text = response.choices[0].message.content.strip()

    try:
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        return json.loads(text)
    except Exception as e:
        print(f"Parse error: {e}")
        print(f"Raw response: {text[:500]}")
        return []

def generate_summary(analyzed_values: list) -> str:
    critical = [v for v in analyzed_values if v.get("status") == "critical"]
    borderline = [v for v in analyzed_values if v.get("status") == "borderline"]

    prompt = f"""Write a 3-4 sentence plain English summary for a patient about their medical report.

Report stats:
- Total tests: {len(analyzed_values)}
- Critical: {len(critical)} ({', '.join([v['test_name'] for v in critical]) if critical else 'none'})
- Borderline: {len(borderline)} ({', '.join([v['test_name'] for v in borderline]) if borderline else 'none'})

Be honest but reassuring. No medical jargon. Always remind them to consult their doctor. Return only the summary text, nothing else."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content.strip()

def analyze_report(extracted_values: list) -> dict:
    analyzed = analyze_all_values(extracted_values)
    summary = generate_summary(analyzed)

    critical = [v for v in analyzed if v.get("status") == "critical"]
    borderline = [v for v in analyzed if v.get("status") == "borderline"]
    normal = [v for v in analyzed if v.get("status") == "normal"]

    doctor_questions = list(set([
        v["doctor_question"] for v in analyzed
        if v.get("concern_level") in ["medium", "high"]
    ]))

    return {
        "summary": summary,
        "total_analyzed": len(analyzed),
        "critical_count": len(critical),
        "borderline_count": len(borderline),
        "normal_count": len(normal),
        "analyzed_values": analyzed,
        "doctor_questions": doctor_questions[:5]
    }