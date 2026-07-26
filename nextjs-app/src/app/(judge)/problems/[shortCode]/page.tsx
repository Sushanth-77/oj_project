"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useState, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import { useSession } from "next-auth/react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Play, RotateCcw, Sparkles, ArrowLeft, Terminal, Tag,
  Bookmark, BookmarkCheck, StickyNote, FileText,
  Lightbulb, ChevronRight, TrendingUp, Users,
} from "lucide-react";
import { CodeEditor } from "@/components/editor/CodeEditor";
import { VerdictBadge } from "@/components/ui/VerdictBadge";
import { Problem, TestCase, Verdict, ProblemStats } from "@/types";

const DEFAULT_BOILERPLATES: Record<string, string> = {
  python: `# input() and print() work just like LeetCode — no sys.stdin needed!\n# Example: a, b = map(int, input().split())\n\n# Write your solution here:\n`,
  cpp: `#include <iostream>\nusing namespace std;\n\nint main() {\n    // cin and cout work naturally!\n    // Example: int a, b; cin >> a >> b; cout << a + b << endl;\n\n    return 0;\n}`,
  c: `#include <stdio.h>\n\nint main() {\n    // scanf and printf work naturally!\n    // Example: int a, b; scanf(\"%d %d\", &a, &b); printf(\"%d\\n\", a + b);\n\n    return 0;\n}`,
};

const DIFF_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  E: { label: "Easy",   color: "text-green-400",  bg: "bg-green-400/20 border-green-400/30" },
  M: { label: "Medium", color: "text-yellow-400", bg: "bg-yellow-400/20 border-yellow-400/30" },
  H: { label: "Hard",   color: "text-red-400",    bg: "bg-red-400/20 border-red-400/30" },
};

type LeftTab = "description" | "notes";

// ─── Stats Bar ──────────────────────────────────────────────────────────────
function StatsBar({ shortCode }: { shortCode: string }) {
  const { data } = useQuery<ProblemStats>({
    queryKey: ["problemStats", shortCode],
    queryFn: async () => {
      const res = await fetch(`/api/problems/${shortCode}/stats`);
      if (!res.ok) throw new Error("stats failed");
      return res.json();
    },
    staleTime: 120_000,
  });

  if (!data) return null;

  const langColors: Record<string, string> = {
    python: "bg-blue-400/70", cpp: "bg-purple-400/70", c: "bg-orange-400/70",
  };

  return (
    <div className="flex flex-wrap items-center gap-4 text-xs text-gray-500 mt-3 pt-3 border-t border-[#2d3748]">
      <div className="flex items-center gap-1.5">
        <TrendingUp className="w-3.5 h-3.5 text-green-400" />
        <span className="text-green-400 font-semibold">{data.acceptanceRate}%</span>
        <span>acceptance</span>
      </div>
      <div className="flex items-center gap-1.5">
        <Users className="w-3.5 h-3.5" />
        <span>{data.total.toLocaleString()} submissions</span>
      </div>
      {data.languageBreakdown.slice(0, 3).map((lang) => (
        <div key={lang.language} className="flex items-center gap-1">
          <div className={`w-2 h-2 rounded-full ${langColors[lang.language] ?? "bg-gray-500"}`} />
          <span className="capitalize">{lang.language} ({lang.count})</span>
        </div>
      ))}
    </div>
  );
}

// ─── Bookmark Button ─────────────────────────────────────────────────────────
function BookmarkButton({ shortCode }: { shortCode: string }) {
  const { data: session } = useSession();
  const queryClient = useQueryClient();

  const { data } = useQuery<{ bookmarked: boolean }>({
    queryKey: ["bookmark", shortCode],
    queryFn: async () => {
      const res = await fetch(`/api/problems/${shortCode}/bookmark`);
      return res.json();
    },
    enabled: !!session,
    staleTime: 60_000,
  });

  const mutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`/api/problems/${shortCode}/bookmark`, { method: "POST" });
      return res.json();
    },
    onSuccess: (result) => {
      queryClient.setQueryData(["bookmark", shortCode], result);
    },
  });

  if (!session) return null;

  const bookmarked = data?.bookmarked ?? false;

  return (
    <button
      onClick={() => mutation.mutate()}
      disabled={mutation.isPending}
      title={bookmarked ? "Remove bookmark" : "Bookmark this problem"}
      className={`p-2 rounded-lg border transition-all ${
        bookmarked
          ? "bg-yellow-400/15 border-yellow-400/40 text-yellow-400 hover:bg-yellow-400/25"
          : "bg-transparent border-[#2d3748] text-gray-500 hover:border-yellow-400/40 hover:text-yellow-400"
      }`}
    >
      {bookmarked ? <BookmarkCheck className="w-4 h-4" /> : <Bookmark className="w-4 h-4" />}
    </button>
  );
}

// ─── Notes Panel ─────────────────────────────────────────────────────────────
function NotesPanel({ shortCode }: { shortCode: string }) {
  const { data: session } = useSession();
  const [content, setContent] = useState("");
  const [saved, setSaved] = useState(true);
  const [saving, setSaving] = useState(false);

  const { data } = useQuery<{ content: string; updatedAt: string | null }>({
    queryKey: ["notes", shortCode],
    queryFn: async () => {
      const res = await fetch(`/api/problems/${shortCode}/notes`);
      return res.json();
    },
    enabled: !!session,
  });

  useEffect(() => {
    if (data?.content !== undefined) setContent(data.content);
  }, [data]);

  const handleSave = useCallback(async () => {
    setSaving(true);
    await fetch(`/api/problems/${shortCode}/notes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content }),
    });
    setSaving(false);
    setSaved(true);
  }, [shortCode, content]);

  // Auto-save after 1.5s of inactivity
  useEffect(() => {
    if (saved) return;
    const timer = setTimeout(handleSave, 1500);
    return () => clearTimeout(timer);
  }, [content, saved, handleSave]);

  if (!session) {
    return (
      <div className="flex flex-col items-center justify-center h-48 gap-3 text-center px-4">
        <StickyNote className="w-8 h-8 text-gray-600" />
        <p className="text-gray-500 text-sm">Sign in to save private notes for this problem.</p>
        <Link href="/login" className="text-[#00d4aa] text-sm hover:underline">Sign in →</Link>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3 h-full">
      <div className="flex items-center justify-between">
        <p className="text-xs text-gray-500">Private notes — only you can see these.</p>
        <span className={`text-xs transition-colors ${saving ? "text-yellow-400" : saved ? "text-green-400" : "text-gray-500"}`}>
          {saving ? "Saving…" : saved ? "✓ Saved" : "Unsaved"}
        </span>
      </div>
      <textarea
        value={content}
        onChange={(e) => { setContent(e.target.value); setSaved(false); }}
        placeholder="Write your approach, observations, or reminders here… (auto-saves)"
        className="flex-1 w-full min-h-[300px] bg-[#0f1419] border border-[#2d3748] rounded-lg p-3 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-[#00d4aa]/50 resize-none font-mono leading-relaxed"
      />
    </div>
  );
}

// ─── AI Hint Panel ───────────────────────────────────────────────────────────
function HintPanel({
  shortCode, code, language, onClose,
}: {
  shortCode: string; code: string; language: string; onClose: () => void;
}) {
  const [level, setLevel] = useState<1 | 2 | 3>(1);
  const [hint, setHint] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchHint = async (l: 1 | 2 | 3) => {
    setLoading(true);
    setHint(null);
    const res = await fetch(`/api/problems/${shortCode}/hint`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ currentCode: code, language, hintLevel: l }),
    });
    const data = await res.json();
    setHint(data.hint || data.error || "Failed to get hint.");
    setLoading(false);
  };

  const levelColors = ["", "text-blue-400", "text-yellow-400", "text-orange-400"];
  const levelLabels = ["", "💡 Conceptual", "🔧 Algorithmic", "🗺️ Near-Solution"];

  return (
    <div className="mt-3 rounded-xl border border-[#00d4aa]/20 bg-[#00d4aa]/5 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2.5 bg-[#00d4aa]/10 border-b border-[#00d4aa]/20">
        <div className="flex items-center gap-2">
          <Lightbulb className="w-4 h-4 text-[#00d4aa]" />
          <span className="text-[#00d4aa] text-sm font-semibold">AI Hint</span>
        </div>
        <button onClick={onClose} className="text-gray-500 hover:text-gray-300 text-xs">✕ Close</button>
      </div>
      <div className="p-4">
        {/* Level selector */}
        <div className="flex gap-2 mb-4">
          {([1, 2, 3] as const).map((l) => (
            <button
              key={l}
              onClick={() => { setLevel(l); fetchHint(l); }}
              className={`flex-1 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                level === l
                  ? `${levelColors[l]} bg-white/5 border-current`
                  : "text-gray-500 border-[#2d3748] hover:border-gray-500"
              }`}
            >
              Level {l}
            </button>
          ))}
        </div>

        {!hint && !loading && (
          <button
            onClick={() => fetchHint(level)}
            className="w-full py-2 rounded-lg bg-[#00d4aa]/20 text-[#00d4aa] text-sm font-semibold hover:bg-[#00d4aa]/30 transition-all"
          >
            Get {levelLabels[level]} Hint
          </button>
        )}

        {loading && (
          <div className="flex items-center justify-center gap-2 py-4 text-[#00d4aa] text-sm">
            <div className="w-4 h-4 border-2 border-t-transparent border-[#00d4aa] rounded-full animate-spin" />
            Generating hint…
          </div>
        )}

        {hint && !loading && (
          <div className="prose prose-invert prose-sm max-w-none text-gray-300 text-xs leading-relaxed">
            <ReactMarkdown>{hint}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────
export default function ProblemDetail() {
  const params = useParams();
  const shortCode = params.shortCode as string;
  const queryClient = useQueryClient();
  const { data: session } = useSession();

  const [language, setLanguage] = useState("python");
  const [code, setCode] = useState("");
  const [hasLoaded, setHasLoaded] = useState(false);
  const [submissionId, setSubmissionId] = useState<number | null>(null);
  const [errorDetail, setErrorDetail] = useState<string | null>(null);
  const [leftTab, setLeftTab] = useState<LeftTab>("description");
  const [showHint, setShowHint] = useState(false);
  const [newBadges, setNewBadges] = useState<string[]>([]);

  const { data: problem, isLoading: problemLoading } = useQuery<Problem>({
    queryKey: ["problem", shortCode],
    queryFn: async () => {
      const res = await fetch(`/api/problems/${shortCode}`);
      if (!res.ok) throw new Error("Failed to fetch problem");
      return res.json();
    },
  });

  // Determine boilerplate: prefer admin-set template, fallback to default
  const getBoilerplate = useCallback((lang: string) => {
    const templates = (problem?.templates as Record<string, string> | null | undefined);
    return templates?.[lang] ?? DEFAULT_BOILERPLATES[lang] ?? "";
  }, [problem]);

  useEffect(() => {
    const storageKey = `code_${shortCode}_${language}`;
    const saved = localStorage.getItem(storageKey);
    if (saved) {
      setCode(saved);
    } else {
      setCode(getBoilerplate(language));
    }
    setHasLoaded(true);
  }, [language, shortCode, getBoilerplate]);

  const handleCodeChange = (newCode: string) => {
    setCode(newCode);
    if (hasLoaded) {
      localStorage.setItem(`code_${shortCode}_${language}`, newCode);
    }
  };

  const handleReset = () => {
    const defaultCode = getBoilerplate(language);
    setCode(defaultCode);
    localStorage.setItem(`code_${shortCode}_${language}`, defaultCode);
  };

  const { data: statusData } = useQuery<{ id: number; status: Verdict }>({
    queryKey: ["submissionStatus", submissionId],
    queryFn: async () => {
      if (!submissionId) return null;
      const res = await fetch(`/api/submissions/${submissionId}/status`);
      if (!res.ok) throw new Error("Failed to fetch status");
      return res.json();
    },
    enabled: !!submissionId,
    refetchInterval: (query) => {
      if (query.state.data && query.state.data.status !== "PE") return false;
      return 1000;
    },
  });

  const { data: aiReview, isLoading: aiReviewLoading, refetch: getAIReview } = useQuery({
    queryKey: ["aiReview", submissionId],
    queryFn: async () => {
      if (!submissionId) return null;
      const res = await fetch(`/api/ai-review/${submissionId}`);
      if (!res.ok) throw new Error("Failed to fetch AI review");
      return res.json();
    },
    enabled: false,
  });

  const submitMutation = useMutation({
    mutationFn: async () => {
      if (!problem) throw new Error("Problem not loaded");
      const res = await fetch("/api/submissions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ problemId: problem.id, codeText: code, language }),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || "Submission failed");
      }
      return res.json();
    },
    onSuccess: (data) => {
      if (submissionId) {
        queryClient.removeQueries({ queryKey: ["submissionStatus", submissionId] });
        queryClient.removeQueries({ queryKey: ["aiReview", submissionId] });
      }
      setSubmissionId(data.id);
      setErrorDetail(data.errorDetail || null);
      queryClient.invalidateQueries({ queryKey: ["submissions"] });
      queryClient.invalidateQueries({ queryKey: ["solvedProblems"] });
      // Show badge notifications if any were awarded
      if (data.newBadges?.length > 0) setNewBadges(data.newBadges);
    },
  });

  if (problemLoading) {
    return <div className="p-8 text-center text-gray-400">Loading problem details...</div>;
  }
  if (!problem) {
    return <div className="p-8 text-center text-red-500">Problem not found.</div>;
  }

  const currentVerdict = statusData?.status;
  const isEvaluating = submitMutation.isPending || currentVerdict === "PE";
  const showErrorPanel = (currentVerdict === "CE" || currentVerdict === "RE") && errorDetail;
  const diff = DIFF_CONFIG[problem.difficulty];

  return (
    <div className="flex flex-col lg:flex-row h-[calc(100vh-64px)] overflow-hidden">

      {/* Badge Toast */}
      {newBadges.length > 0 && (
        <div className="fixed top-20 right-4 z-50 flex flex-col gap-2">
          {newBadges.map((slug) => (
            <div key={slug} className="bg-yellow-400/20 border border-yellow-400/50 text-yellow-300 px-4 py-2.5 rounded-xl text-sm font-semibold shadow-lg animate-pulse">
              🏅 New badge unlocked: {slug.replace(/_/g, " ")}!
            </div>
          ))}
          <button onClick={() => setNewBadges([])} className="text-xs text-gray-500 hover:text-gray-300 text-right mt-1">Dismiss</button>
        </div>
      )}

      {/* Left side: Problem Description / Notes */}
      <div className="w-full lg:w-1/2 h-full flex flex-col bg-[#1a1f29] border-r border-[#2d3748]">
        {/* Tab bar */}
        <div className="flex items-center gap-0 border-b border-[#2d3748] px-4 flex-shrink-0">
          <button
            onClick={() => setLeftTab("description")}
            className={`flex items-center gap-1.5 px-3 py-3 text-sm font-medium border-b-2 transition-colors ${
              leftTab === "description"
                ? "border-[#00d4aa] text-[#00d4aa]"
                : "border-transparent text-gray-500 hover:text-gray-300"
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            Description
          </button>
          <button
            onClick={() => setLeftTab("notes")}
            className={`flex items-center gap-1.5 px-3 py-3 text-sm font-medium border-b-2 transition-colors ${
              leftTab === "notes"
                ? "border-[#00d4aa] text-[#00d4aa]"
                : "border-transparent text-gray-500 hover:text-gray-300"
            }`}
          >
            <StickyNote className="w-3.5 h-3.5" />
            Notes
          </button>

          {/* Spacer + Bookmark */}
          <div className="ml-auto flex items-center gap-2 py-2">
            <BookmarkButton shortCode={shortCode} />
          </div>
        </div>

        {/* Panel content */}
        <div className="flex-1 overflow-y-auto p-6">
          {leftTab === "description" ? (
            <>
              <div className="mb-4">
                <Link href="/problems" className="inline-flex items-center text-sm font-medium text-[#00d4aa] hover:text-[#00b38f] transition-colors">
                  <ArrowLeft className="w-4 h-4 mr-1" />
                  Back to Problems
                </Link>
              </div>

              <div className="flex justify-between items-start mb-4">
                <h1 className="text-2xl font-bold text-white leading-tight">{problem.name}</h1>
                <span className={`px-3 py-1 rounded-full text-sm font-bold border ml-3 flex-shrink-0 ${diff.bg} ${diff.color}`}>
                  {diff.label}
                </span>
              </div>

              {/* Stats bar */}
              <StatsBar shortCode={shortCode} />

              {/* Problem statement */}
              <div className="mt-5 text-gray-200 leading-relaxed
                [&_h1]:text-white [&_h1]:font-bold [&_h1]:text-2xl [&_h1]:mt-6 [&_h1]:mb-3
                [&_h2]:text-white [&_h2]:font-bold [&_h2]:text-xl  [&_h2]:mt-6 [&_h2]:mb-3
                [&_h3]:text-white [&_h3]:font-bold [&_h3]:text-lg  [&_h3]:mt-4 [&_h3]:mb-2
                [&_p]:text-gray-200 [&_p]:mb-3
                [&_ul]:list-disc [&_ul]:pl-5 [&_ul]:text-gray-200 [&_ul]:mb-3
                [&_ol]:list-decimal [&_ol]:pl-5 [&_ol]:text-gray-200 [&_ol]:mb-3
                [&_li]:mb-1
                [&_strong]:text-white [&_strong]:font-semibold
                [&_em]:text-gray-300
                [&_code]:bg-[#2d3748] [&_code]:text-[#00d4aa] [&_code]:px-1.5 [&_code]:py-0.5 [&_code]:rounded [&_code]:text-sm [&_code]:font-mono
                [&_pre]:bg-[#0f1419] [&_pre]:border [&_pre]:border-[#2d3748] [&_pre]:rounded-lg [&_pre]:p-4 [&_pre]:overflow-x-auto [&_pre]:my-4
                [&_pre_code]:bg-transparent [&_pre_code]:text-gray-200 [&_pre_code]:p-0
                [&_blockquote]:border-l-4 [&_blockquote]:border-[#00d4aa] [&_blockquote]:pl-4 [&_blockquote]:text-gray-400 [&_blockquote]:italic
                [&_a]:text-[#00d4aa] [&_a]:hover:underline
                [&_hr]:border-[#2d3748] [&_hr]:my-6
                [&_table]:w-full [&_table]:text-sm
                [&_th]:text-left [&_th]:text-gray-400 [&_th]:border-b [&_th]:border-[#2d3748] [&_th]:pb-2
                [&_td]:text-gray-200 [&_td]:py-2 [&_td]:border-b [&_td]:border-[#2d3748]/50">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {problem.statement}
                </ReactMarkdown>
              </div>

              {/* Sample Test Cases */}
              {problem.testCases && problem.testCases.length > 0 && (
                <div className="mt-8 space-y-4">
                  <h3 className="text-xl font-bold text-white border-b border-[#2d3748] pb-2">Sample Test Cases</h3>
                  {problem.testCases.map((tc: TestCase) => (
                    <div key={tc.id} className="bg-[#0f1419] rounded-lg p-4 border border-[#2d3748]">
                      <div className="mb-2">
                        <strong className="text-sm text-[#a0aec0] block mb-1">Input:</strong>
                        <pre className="bg-[#2d3748] p-2 rounded text-sm font-mono border border-[#4a5568] text-gray-200 whitespace-pre-wrap">{tc.input}</pre>
                      </div>
                      <div>
                        <strong className="text-sm text-[#a0aec0] block mb-1">Expected Output:</strong>
                        <pre className="bg-[#2d3748] p-2 rounded text-sm font-mono border border-[#4a5568] text-gray-200 whitespace-pre-wrap">{tc.output}</pre>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Topic Tags */}
              {problem.topics && problem.topics.length > 0 && (
                <div className="mt-6 pt-5 border-t border-[#2d3748]">
                  <div className="flex items-center gap-2 mb-3">
                    <Tag className="w-3.5 h-3.5 text-gray-500" />
                    <span className="text-xs text-gray-500 uppercase tracking-wider font-semibold">Topics</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {problem.topics.map((topic: string) => (
                      <span key={topic} className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-[#00d4aa]/10 text-[#00d4aa] border border-[#00d4aa]/25 font-medium">
                        {topic}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <NotesPanel shortCode={shortCode} />
          )}
        </div>
      </div>

      {/* Right side: Code Editor & Result */}
      <div className="w-full lg:w-1/2 h-full flex flex-col bg-[#0f1419]">
        {/* Editor toolbar */}
        <div className="flex items-center justify-between px-4 py-2 bg-[#1a1f29] border-b border-[#2d3748]">
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="bg-[#2d3748] text-white border border-[#4a5568] rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-[#00d4aa]"
          >
            <option value="python">Python 3</option>
            <option value="cpp">C++</option>
            <option value="c">C</option>
          </select>

          <div className="flex items-center gap-2">
            {/* AI Hint toggle */}
            {session && (
              <button
                onClick={() => setShowHint(!showHint)}
                title="Get a hint"
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                  showHint
                    ? "bg-[#00d4aa]/20 border-[#00d4aa]/50 text-[#00d4aa]"
                    : "bg-transparent border-[#2d3748] text-gray-400 hover:border-[#00d4aa]/40 hover:text-[#00d4aa]"
                }`}
              >
                <Lightbulb className="w-3.5 h-3.5" />
                Hint
              </button>
            )}
            <button
              onClick={handleReset}
              className="text-gray-400 hover:text-white transition-colors p-1.5"
              title="Reset code to default boilerplate"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Code editor */}
        <div className="flex-1 overflow-hidden relative">
          <CodeEditor
            value={code}
            language={language}
            onChange={handleCodeChange}
            height="100%"
          />
        </div>

        {/* Bottom action bar */}
        <div className="bg-[#1a1f29] border-t border-[#2d3748] p-4 flex-shrink-0">
          <div className="flex justify-between items-center mb-3">
            <div className="flex items-center gap-4">
              {isEvaluating ? (
                <div className="flex items-center gap-2 text-[#00d4aa]">
                  <div className="w-4 h-4 border-2 border-t-transparent border-[#00d4aa] rounded-full animate-spin" />
                  <span className="text-sm font-medium">Evaluating...</span>
                </div>
              ) : currentVerdict ? (
                <VerdictBadge verdict={currentVerdict} />
              ) : (
                <span className="text-gray-500 text-sm">Ready to submit</span>
              )}
            </div>

            <div className="flex gap-3">
              {currentVerdict && currentVerdict !== "PE" && (
                <button
                  onClick={() => getAIReview()}
                  disabled={aiReviewLoading}
                  className="btn btn-secondary flex items-center gap-2 text-sm px-3 py-1.5"
                >
                  <Sparkles className="w-4 h-4 text-purple-400" />
                  {aiReviewLoading ? "Reviewing..." : "AI Review"}
                </button>
              )}

              <button
                onClick={() => submitMutation.mutate()}
                disabled={isEvaluating || !code.trim()}
                className="btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 text-sm px-4 py-1.5"
              >
                <Play className="w-4 h-4" />
                Submit Code
              </button>
            </div>
          </div>

          {/* Hint panel */}
          {showHint && (
            <HintPanel
              shortCode={shortCode}
              code={code}
              language={language}
              onClose={() => setShowHint(false)}
            />
          )}

          {/* CE/RE error panel */}
          {showErrorPanel && !showHint && (
            <div className="mt-2 rounded-lg border border-red-500/30 bg-red-500/5 overflow-hidden">
              <div className="flex items-center gap-2 px-4 py-2 bg-red-500/10 border-b border-red-500/20">
                <Terminal className="w-4 h-4 text-red-400" />
                <span className="text-red-400 text-sm font-semibold">
                  {currentVerdict === "CE" ? "Compilation Error" : "Runtime Error"}
                </span>
              </div>
              <pre className="px-4 py-3 text-red-300 text-xs font-mono whitespace-pre-wrap overflow-x-auto max-h-40">
                {errorDetail}
              </pre>
            </div>
          )}

          {/* AI Review panel */}
          {aiReview && aiReview.success && !showHint && (
            <div className="mt-3 max-h-48 overflow-y-auto p-4 bg-[#2d3748] rounded-lg border border-purple-500/30 prose prose-invert prose-sm max-w-none">
              <ReactMarkdown>{aiReview.review}</ReactMarkdown>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
