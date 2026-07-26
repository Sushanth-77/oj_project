"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import Link from "next/link";
import { format } from "date-fns";
import { ArrowLeft, Copy, Check, Lock, ExternalLink } from "lucide-react";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { VerdictBadge } from "@/components/ui/VerdictBadge";

const LANG_LABELS: Record<string, string> = {
  python: "Python 3", cpp: "C++", c: "C",
};

const DIFF_CONFIG: Record<string, { label: string; color: string }> = {
  E: { label: "Easy",   color: "text-green-400" },
  M: { label: "Medium", color: "text-yellow-400" },
  H: { label: "Hard",   color: "text-red-400" },
};

export default function SubmissionDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [copied, setCopied] = useState(false);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["submission", id],
    queryFn: async () => {
      const res = await fetch(`/api/submissions/${id}`);
      if (!res.ok) throw new Error("Not found");
      return res.json();
    },
  });

  const handleCopy = async () => {
    await navigator.clipboard.writeText(window.location.href);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleCopyCode = async () => {
    if (data?.codeText) {
      await navigator.clipboard.writeText(data.codeText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0f1419] flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-t-transparent border-[#00d4aa] rounded-full animate-spin" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="min-h-screen bg-[#0f1419] flex flex-col items-center justify-center gap-4">
        <p className="text-red-400 text-lg">Submission not found.</p>
        <Link href="/submissions" className="text-[#00d4aa] hover:underline">← Back to submissions</Link>
      </div>
    );
  }

  const diff = DIFF_CONFIG[data.problem?.difficulty] ?? { label: "?", color: "text-gray-400" };

  return (
    <div className="min-h-screen bg-[#0f1419]">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">

        {/* Back nav */}
        <Link href="/submissions" className="inline-flex items-center gap-1 text-sm text-[#00d4aa] hover:text-[#00b38f] mb-6 transition-colors">
          <ArrowLeft className="w-4 h-4" />
          Back to My Submissions
        </Link>

        {/* Header card */}
        <div className="bg-[#1a1f29] rounded-2xl border border-[#2d3748] p-6 mb-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <h1 className="text-xl font-bold text-white">Submission #{data.id}</h1>
                <VerdictBadge verdict={data.verdict} />
              </div>
              <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-gray-400">
                {data.problem && (
                  <Link
                    href={`/problems/${data.problem.shortCode}`}
                    className="flex items-center gap-1 text-[#00d4aa] hover:text-[#00b38f] font-medium transition-colors"
                  >
                    {data.problem.name}
                    <ExternalLink className="w-3 h-3" />
                  </Link>
                )}
                {data.problem && (
                  <span className={`font-medium ${diff.color}`}>{diff.label}</span>
                )}
                <span className="bg-[#2d3748] px-2 py-0.5 rounded text-xs font-medium">
                  {LANG_LABELS[data.language] ?? data.language}
                </span>
                <span className="text-gray-500 text-xs">
                  {format(new Date(data.submitted), "MMM d, yyyy · h:mm a")}
                </span>
              </div>
              {/* Submitted by */}
              {data.user?.name && (
                <p className="text-xs text-gray-600 mt-1">
                  by{" "}
                  <Link href={`/profile/${data.user.id}`} className="text-gray-400 hover:text-white transition-colors">
                    {data.user.name}
                  </Link>
                </p>
              )}
            </div>

            {/* Share button */}
            <button
              onClick={handleCopy}
              className="flex items-center gap-2 px-4 py-2 rounded-lg border border-[#2d3748] text-sm text-gray-400 hover:border-[#00d4aa]/40 hover:text-[#00d4aa] transition-all flex-shrink-0"
            >
              {copied ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
              {copied ? "Copied!" : "Copy Link"}
            </button>
          </div>
        </div>

        {/* Code section */}
        <div className="bg-[#1a1f29] rounded-xl border border-[#2d3748] overflow-hidden">
          <div className="flex items-center justify-between px-5 py-3 border-b border-[#2d3748]">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-red-400" />
              <div className="w-2 h-2 rounded-full bg-yellow-400" />
              <div className="w-2 h-2 rounded-full bg-green-400" />
              <span className="ml-3 text-sm font-medium text-gray-400">
                {LANG_LABELS[data.language] ?? data.language}
              </span>
            </div>
            {data.canViewCode && (
              <button
                onClick={handleCopyCode}
                className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-white transition-colors"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5" />}
                Copy Code
              </button>
            )}
          </div>

          {data.canViewCode ? (
            <pre className="p-6 text-sm font-mono text-gray-200 overflow-x-auto leading-relaxed whitespace-pre">
              {data.codeText}
            </pre>
          ) : (
            <div className="flex flex-col items-center justify-center py-16 gap-3">
              <Lock className="w-10 h-10 text-gray-600" />
              <p className="text-gray-500 text-sm">Code is private — only the author can view it.</p>
              <Link href="/login" className="text-[#00d4aa] text-sm hover:underline">Sign in to view your own submissions →</Link>
            </div>
          )}
        </div>

        {/* Problem link */}
        {data.problem && (
          <div className="mt-4 text-center">
            <Link
              href={`/problems/${data.problem.shortCode}`}
              className="inline-flex items-center gap-2 text-sm text-[#00d4aa] hover:text-[#00b38f] transition-colors"
            >
              Try this problem yourself
              <ChevronRight className="w-4 h-4" />
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}

function ChevronRight({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
    </svg>
  );
}
