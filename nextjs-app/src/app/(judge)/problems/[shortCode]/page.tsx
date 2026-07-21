"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Play, RotateCcw, Sparkles, ArrowLeft, Terminal } from "lucide-react";
import { CodeEditor } from "@/components/editor/CodeEditor";
import { VerdictBadge } from "@/components/ui/VerdictBadge";
import { Problem, TestCase, Verdict } from "@/types";

// Fix 3: Only Python, C++, C
// Fix 5: LeetCode-style boilerplates — use input()/print(), cin/cout, scanf/printf naturally
const BOILERPLATES: Record<string, string> = {
  python: `# input() and print() work just like LeetCode — no sys.stdin needed!
# Example: a, b = map(int, input().split())

# Write your solution here:
`,
  cpp: `#include <iostream>
using namespace std;

int main() {
    // cin and cout work naturally — just like LeetCode!
    // Example: int a, b; cin >> a >> b; cout << a + b << endl;

    return 0;
}`,
  c: `#include <stdio.h>

int main() {
    // scanf and printf work naturally!
    // Example: int a, b; scanf("%d %d", &a, &b); printf("%d\\n", a + b);

    return 0;
}`,
};

export default function ProblemDetail() {
  const params = useParams();
  const shortCode = params.shortCode as string;
  const queryClient = useQueryClient();

  const [language, setLanguage] = useState("python");
  const [code, setCode] = useState("");
  const [hasLoaded, setHasLoaded] = useState(false);
  const [submissionId, setSubmissionId] = useState<number | null>(null);
  // Fix 4: store CE/RE error detail from POST response
  const [errorDetail, setErrorDetail] = useState<string | null>(null);

  useEffect(() => {
    const storageKey = `code_${shortCode}_${language}`;
    const saved = localStorage.getItem(storageKey);
    if (saved) {
      setCode(saved);
    } else {
      setCode(BOILERPLATES[language] || "");
    }
    setHasLoaded(true);
  }, [language, shortCode]);

  const handleCodeChange = (newCode: string) => {
    setCode(newCode);
    if (hasLoaded) {
      localStorage.setItem(`code_${shortCode}_${language}`, newCode);
    }
  };

  const handleReset = () => {
    const defaultCode = BOILERPLATES[language] || "";
    setCode(defaultCode);
    localStorage.setItem(`code_${shortCode}_${language}`, defaultCode);
  };

  const { data: problem, isLoading: problemLoading } = useQuery<Problem>({
    queryKey: ["problem", shortCode],
    queryFn: async () => {
      const res = await fetch(`/api/problems/${shortCode}`);
      if (!res.ok) throw new Error("Failed to fetch problem");
      return res.json();
    },
  });

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
        body: JSON.stringify({
          problemId: problem.id,
          codeText: code,
          language,
        }),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || "Submission failed");
      }
      return res.json();
    },
    onSuccess: (data) => {
      // Remove old submission queries before setting new one
      if (submissionId) {
        queryClient.removeQueries({ queryKey: ["submissionStatus", submissionId] });
        queryClient.removeQueries({ queryKey: ["aiReview", submissionId] });
      }
      setSubmissionId(data.id);
      // Fix 4: capture error detail from the synchronous POST response
      setErrorDetail(data.errorDetail || null);
      queryClient.invalidateQueries({ queryKey: ["submissions"] });
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
  // Fix 4: show error panel for CE or RE
  const showErrorPanel = (currentVerdict === "CE" || currentVerdict === "RE") && errorDetail;

  return (
    <div className="flex flex-col lg:flex-row h-[calc(100vh-64px)] overflow-hidden">
      {/* Left side: Problem Description */}
      <div className="w-full lg:w-1/2 h-full overflow-y-auto bg-[#1a1f29] border-r border-[#2d3748] p-6">
        <div className="mb-4">
          <Link href="/problems" className="inline-flex items-center text-sm font-medium text-[#00d4aa] hover:text-[#00b38f] transition-colors">
            <ArrowLeft className="w-4 h-4 mr-1" />
            Back to Problems
          </Link>
        </div>
        
        <div className="mb-6 flex justify-between items-center">
          <h1 className="text-3xl font-bold text-white">{problem.name}</h1>
          <span className={`px-3 py-1 rounded-full text-sm font-bold ${
            problem.difficulty === 'E' ? 'bg-green-400/20 text-green-400 border border-green-400/30' :
            problem.difficulty === 'M' ? 'bg-yellow-400/20 text-yellow-400 border border-yellow-400/30' :
            'bg-red-400/20 text-red-400 border border-red-400/30'
          }`}>
            {problem.difficulty === 'E' ? 'Easy' : problem.difficulty === 'M' ? 'Medium' : 'Hard'}
          </span>
        </div>

        <div className="prose max-w-none prose-invert">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {problem.statement}
          </ReactMarkdown>
        </div>

        {problem.testCases && problem.testCases.length > 0 && (
          <div className="mt-8 space-y-4">
            <h3 className="text-xl font-bold text-white border-b border-[#2d3748] pb-2">Sample Test Cases</h3>
            {problem.testCases.map((tc: TestCase, i: number) => (
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
      </div>

      {/* Right side: Code Editor & Result */}
      <div className="w-full lg:w-1/2 h-full flex flex-col bg-[#0f1419]">
        <div className="flex items-center justify-between px-4 py-2 bg-[#1a1f29] border-b border-[#2d3748]">
          {/* Fix 3: Only Python, C++, C */}
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="bg-[#2d3748] text-white border border-[#4a5568] rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-[#00d4aa]"
          >
            <option value="python">Python 3</option>
            <option value="cpp">C++</option>
            <option value="c">C</option>
          </select>
          
          <button
            onClick={handleReset}
            className="text-gray-400 hover:text-white transition-colors"
            title="Reset code to default boilerplate"
          >
            <RotateCcw className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 overflow-hidden relative">
           <CodeEditor
             value={code}
             language={language}
             onChange={handleCodeChange}
             height="100%"
           />
        </div>

        <div className="bg-[#1a1f29] border-t border-[#2d3748] p-4">
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
                  className="btn btn-secondary flex items-center gap-2"
                >
                  <Sparkles className="w-4 h-4 text-purple-400" />
                  {aiReviewLoading ? "Reviewing..." : "Get AI Review"}
                </button>
              )}
              
              <button
                onClick={() => submitMutation.mutate()}
                disabled={isEvaluating || !code.trim()}
                className="btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                <Play className="w-4 h-4" />
                Submit Code
              </button>
            </div>
          </div>

          {/* Fix 4: Compilation / Runtime Error Panel */}
          {showErrorPanel && (
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

          {/* AI Review Panel */}
          {aiReview && aiReview.success && (
            <div className="mt-3 max-h-48 overflow-y-auto p-4 bg-[#2d3748] rounded-lg border border-purple-500/30 prose prose-invert prose-sm max-w-none">
              <ReactMarkdown>{aiReview.review}</ReactMarkdown>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
