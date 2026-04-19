"use client";
import { useState } from "react";
import Link from "next/link";

interface AnalyzedValue {
  test_name: string;
  value: string;
  unit: string;
  reference_range: string;
  status: "normal" | "borderline" | "critical" | "unknown";
  explanation: string;
  concern_level: string;
  doctor_question: string;
}

interface Analysis {
  summary: string;
  total_analyzed: number;
  critical_count: number;
  borderline_count: number;
  normal_count: number;
  analyzed_values: AnalyzedValue[];
  doctor_questions: string[];
}

interface Result {
  file_name: string;
  analysis: Analysis;
}
const statusColors = {
  normal: "bg-green-50 border-green-200 text-green-800",
  borderline: "bg-yellow-50 border-yellow-200 text-yellow-800",
  critical: "bg-red-50 border-red-200 text-red-800",
  unknown: "bg-gray-100 border-gray-300 text-gray-700", // darker than before
};

const statusDot = {
  normal: "bg-green-400",
  borderline: "bg-yellow-400",
  critical: "bg-red-500",
  unknown: "bg-gray-400",
};

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [askingQuestion, setAskingQuestion] = useState(false);
  const [filter, setFilter] = useState<
    "all" | "critical" | "borderline" | "normal"
  >("all");

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected) {
      setFile(selected);
      setResult(null);
      setError(null);
      setAnswer(null);
      setFilter("all");
    }
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/analyze`,
        { method: "POST", body: formData },
      );

      if (!response.ok) throw new Error("Analysis failed");
      const data = await response.json();
      if (data.error) {
        setError(data.error);
        return;
      }
      setResult(data);
    } catch {
      setError("Failed to analyze report. Make sure the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  const handleAskQuestion = async () => {
    if (!question.trim() || !result) return;
    setAskingQuestion(true);

    try {
      const reportContext = result.analysis.analyzed_values
        .map((v) => `${v.test_name}: ${v.value} ${v.unit} (${v.status})`)
        .join(", ");

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, report_context: reportContext }),
      });

      const data = await response.json();
      setAnswer(data.answer);
    } catch {
      setAnswer("Failed to get answer. Please try again.");
    } finally {
      setAskingQuestion(false);
    }
  };

  const filteredValues = result
    ? result.analysis.analyzed_values.filter(
        (item) => filter === "all" || item.status === filter,
      )
    : [];

  return (
    <main className="min-h-screen bg-gray-50 py-10 px-4">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center mb-2">
          <h1 className="text-3xl font-semibold text-gray-900 mb-1">
            MediScan
          </h1>
          <p className="text-gray-500 text-sm">
            Upload your medical report and get a plain English explanation
          </p>
          <Link
            href="/history"
            className="text-xs text-gray-400 hover:text-gray-600 underline mt-1 inline-block"
          >
            View report history
          </Link>
        </div>

        {/* Upload — full width */}
        <div className="bg-white rounded-2xl border border-gray-200 p-6">
          <label className="block w-full cursor-pointer">
            <div className="border-2 border-dashed border-gray-300 rounded-xl py-8 text-center hover:border-gray-400 transition-colors">
              <p className="text-gray-400 text-sm">
                {file ? file.name : "Click to upload your medical report PDF"}
              </p>
              <p className="text-gray-300 text-xs mt-1">PDF files only</p>
            </div>
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileChange}
              className="hidden"
            />
          </label>

          {file && (
            <div className="mt-4 flex justify-end">
              <button
                onClick={handleAnalyze}
                disabled={loading}
                className="bg-gray-900 text-white text-sm px-6 py-2 rounded-lg hover:bg-gray-700 disabled:opacity-50 transition-colors"
              >
                {loading
                  ? "Analyzing... (this takes ~30 seconds)"
                  : "Analyze Report"}
              </button>
            </div>
          )}
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 text-sm rounded-xl p-4">
            {error}
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="space-y-6">
            {/* Row 1: Summary (left) + Stats (right) */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Summary / Description */}
              <div className="bg-white rounded-2xl border border-gray-200 p-6 flex flex-col justify-between md:col-span-2">
                <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3">
                  Overall Summary
                </h2>
                <p className="text-gray-800 text-sm leading-relaxed flex-1">
                  {result.analysis.summary}
                </p>
              </div>

              {/* Stats */}
              <div className="bg-white rounded-2xl border border-gray-200 p-6">
                <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3">
                  Results Overview
                </h2>
                <div className="grid grid-cols-1 gap-3">
                  <div className="bg-green-50 rounded-xl p-3 flex items-center justify-between">
                    <p className="text-sm font-medium text-green-600">Normal</p>
                    <p className="text-xl font-semibold text-green-700">
                      {result.analysis.normal_count}
                    </p>
                  </div>
                  <div className="bg-yellow-50 rounded-xl p-3 flex items-center justify-between">
                    <p className="text-sm font-medium text-yellow-600">
                      Borderline
                    </p>
                    <p className="text-xl font-semibold text-yellow-700">
                      {result.analysis.borderline_count}
                    </p>
                  </div>
                  <div className="bg-red-50 rounded-xl p-3 flex items-center justify-between">
                    <p className="text-sm font-medium text-red-600">Critical</p>
                    <p className="text-xl font-semibold text-red-700">
                      {result.analysis.critical_count}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Row 2: Test Results grid */}
            <div className="bg-white rounded-2xl border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wide">
                  Test Results
                </h2>

                {/* Filter tabs */}
                <div className="flex gap-2">
                  {(["all", "critical", "borderline", "normal"] as const).map(
                    (tab) => {
                      const count =
                        tab === "all"
                          ? result.analysis.analyzed_values.length
                          : result.analysis.analyzed_values.filter(
                              (v) => v.status === tab,
                            ).length;
                      const activeStyles: Record<string, string> = {
                        all: "bg-gray-900 text-white",
                        critical: "bg-red-500 text-white",
                        borderline: "bg-yellow-400 text-white",
                        normal: "bg-green-500 text-white",
                      };
                      const isActive = filter === tab;
                      return (
                        <button
                          key={tab}
                          onClick={() => setFilter(tab)}
                          className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-colors ${
                            isActive
                              ? activeStyles[tab]
                              : "bg-gray-100 text-gray-500 hover:bg-gray-200"
                          }`}
                        >
                          {tab} ({count})
                        </button>
                      );
                    },
                  )}
                </div>
              </div>

              {/* 2-column card grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {filteredValues.map((item, i) => (
                  <div
                    key={i}
                    className={`border rounded-xl p-4 ${statusColors[item.status] ?? statusColors.unknown}`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span
                          className={`w-2 h-2 rounded-full flex-shrink-0 ${statusDot[item.status] ?? statusDot.unknown}`}
                        />
                        <span className="font-medium text-sm">
                          {item.test_name}
                        </span>
                      </div>
                      <span className="text-sm font-semibold whitespace-nowrap ml-2">
                        {item.value} {item.unit}
                      </span>
                    </div>
                    <p className="text-xs opacity-75 mb-1">
                      Reference: {item.reference_range}
                    </p>
                    <p className="text-sm">{item.explanation}</p>
                  </div>
                ))}

                {filteredValues.length === 0 && (
                  <p className="text-sm text-gray-400 text-center py-6 col-span-2">
                    No {filter} results.
                  </p>
                )}
              </div>
            </div>

            {/* Doctor Questions */}
            {result.analysis.doctor_questions.length > 0 && (
              <div className="bg-white rounded-2xl border border-gray-200 p-6">
                <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3">
                  Questions to ask your doctor
                </h2>
                <ul className="space-y-2">
                  {result.analysis.doctor_questions.map((q, i) => (
                    <li key={i} className="flex gap-2 text-sm text-gray-700">
                      <span className="text-gray-400 flex-shrink-0">
                        {i + 1}.
                      </span>
                      {q}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Follow-up Q&A */}
            <div className="bg-white rounded-2xl border border-gray-200 p-6">
              <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3">
                Ask a follow-up question
              </h2>
              <div className="flex gap-3">
                <input
                  type="text"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="e.g. Should I be worried about my WBC count?"
                  className="flex-1 border border-gray-200 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-gray-400 text-black"
                  onKeyDown={(e) => e.key === "Enter" && handleAskQuestion()}
                />
                <button
                  onClick={handleAskQuestion}
                  disabled={askingQuestion}
                  className="bg-gray-900 text-white text-sm px-4 py-2 rounded-lg hover:bg-gray-700 disabled:opacity-50 transition-colors"
                >
                  {askingQuestion ? "..." : "Ask"}
                </button>
              </div>
              {answer && (
                <div className="mt-4 bg-gray-50 rounded-xl p-4">
                  <p className="text-sm text-gray-700 leading-relaxed">
                    {answer}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
