"use client";
import { useEffect, useState } from "react";
import Link from "next/link";

interface Report {
  id: string;
  file_name: string;
  summary: string;
  total_analyzed: number;
  critical_count: number;
  borderline_count: number;
  normal_count: number;
  analyzed_values: any[];
  doctor_questions: string[];
  created_at: string;
}

const statusColors: Record<string, string> = {
  normal: "bg-green-50 border-green-200 text-green-800",
  borderline: "bg-yellow-50 border-yellow-200 text-yellow-800",
  critical: "bg-red-50 border-red-200 text-red-800",
  unknown: "bg-gray-50 border-gray-200 text-gray-800",
};

const statusDot: Record<string, string> = {
  normal: "bg-green-400",
  borderline: "bg-yellow-400",
  critical: "bg-red-500",
  unknown: "bg-gray-400",
};

export default function History() {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/reports")
      .then((res) => res.json())
      .then((data) => {
        setReports(data.reports || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <main className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-3xl mx-auto">

        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">
              Report History
            </h1>
            <p className="text-gray-500 text-sm mt-1">
              All previously analyzed medical reports
            </p>
          </div>
          <Link
            href="/"
            className="bg-gray-900 text-white text-sm px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors"
          >
            New Report
          </Link>
        </div>

        {loading && (
          <p className="text-gray-400 text-sm text-center py-12">
            Loading reports...
          </p>
        )}

        {!loading && reports.length === 0 && (
          <p className="text-gray-400 text-sm text-center py-12">
            No reports yet. Upload your first medical report!
          </p>
        )}

        <div className="space-y-4">
          {reports.map((report) => (
            <div
              key={report.id}
              className="bg-white rounded-2xl border border-gray-200 p-6"
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {report.file_name}
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    {new Date(report.created_at).toLocaleString()}
                  </p>
                </div>
                <button
                  onClick={() =>
                    setExpanded(expanded === report.id ? null : report.id)
                  }
                  className="text-xs text-gray-500 hover:text-gray-900 border border-gray-200 px-3 py-1 rounded-lg transition-colors"
                >
                  {expanded === report.id ? "Hide" : "View details"}
                </button>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-3 gap-3 mb-4">
                <div className="bg-green-50 rounded-xl p-3 text-center">
                  <p className="text-xl font-semibold text-green-700">
                    {report.normal_count}
                  </p>
                  <p className="text-xs text-green-600 mt-1">Normal</p>
                </div>
                <div className="bg-yellow-50 rounded-xl p-3 text-center">
                  <p className="text-xl font-semibold text-yellow-700">
                    {report.borderline_count}
                  </p>
                  <p className="text-xs text-yellow-600 mt-1">Borderline</p>
                </div>
                <div className="bg-red-50 rounded-xl p-3 text-center">
                  <p className="text-xl font-semibold text-red-700">
                    {report.critical_count}
                  </p>
                  <p className="text-xs text-red-600 mt-1">Critical</p>
                </div>
              </div>

              {/* Summary */}
              <p className="text-sm text-gray-600 leading-relaxed">
                {report.summary}
              </p>

              {/* Expanded details */}
              {expanded === report.id && (
                <div className="mt-4 border-t border-gray-100 pt-4 space-y-3">
                  <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">
                    Test Results
                  </p>
                  {report.analyzed_values.map((item: any, i: number) => (
                    <div
                      key={i}
                      className={`border rounded-xl p-4 ${statusColors[item.status] || statusColors.unknown}`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2">
                          <span className={`w-2 h-2 rounded-full ${statusDot[item.status] || statusDot.unknown}`} />
                          <span className="font-medium text-sm">
                            {item.test_name}
                          </span>
                        </div>
                        <span className="text-sm font-semibold">
                          {item.value} {item.unit}
                        </span>
                      </div>
                      <p className="text-xs opacity-75 mb-1">
                        Reference: {item.reference_range}
                      </p>
                      <p className="text-sm">{item.explanation}</p>
                    </div>
                  ))}

                  {report.doctor_questions.length > 0 && (
                    <div className="mt-4">
                      <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-2">
                        Questions for your doctor
                      </p>
                      <ul className="space-y-1">
                        {report.doctor_questions.map((q: string, i: number) => (
                          <li key={i} className="flex gap-2 text-sm text-gray-700">
                            <span className="text-gray-400 flex-shrink-0">{i + 1}.</span>
                            {q}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}