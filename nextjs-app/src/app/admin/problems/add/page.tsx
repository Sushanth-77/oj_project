"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { PlusCircle, Trash2, Save, ArrowLeft, Eye, Edit3 } from "lucide-react";
import Link from "next/link";
import { z } from "zod";
import { createProblemSchema } from "@/lib/validations";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type ProblemFormData = z.infer<typeof createProblemSchema>;

export default function AdminAddProblem() {
  const router = useRouter();
  const queryClient = useQueryClient();

  const [formData, setFormData] = useState<ProblemFormData>({
    name: "",
    shortCode: "",
    statement: "",
    difficulty: "E",
    testCases: [],
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [previewMode, setPreviewMode] = useState(false);

  const mutation = useMutation({
    mutationFn: async (data: ProblemFormData) => {
      const res = await fetch("/api/admin/problems", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.error || "Failed to create problem");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["adminProblems"] });
      router.push("/admin/problems");
    },
    onError: (error: Error) => {
      setErrors({ submit: error.message });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    try {
      createProblemSchema.parse(formData);
      setErrors({});
      mutation.mutate(formData);
    } catch (error: any) {
      if (error instanceof z.ZodError) {
        const newErrors: Record<string, string> = {};
        (error as any).errors.forEach((err: any) => {
          if (err.path.length > 0) {
            newErrors[err.path.join(".")] = err.message;
          }
        });
        setErrors(newErrors);
      }
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result as string;
      if (!content) return;

      // Split test cases by 2+ blank lines
      const blocks = content.split(/\n\s*\n/).filter(b => b.trim() !== "");

      const newTestCases: { input: string; output: string; isHidden: boolean; order: number }[] = [];

      blocks.forEach((block, index) => {
        const lines = block.trim().split(/\r?\n/);
        const inputLines: string[] = [];
        const outputLines: string[] = [];

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith("I:")) {
            inputLines.push(trimmed.slice(2).trim());
          } else if (trimmed.startsWith("O:")) {
            outputLines.push(trimmed.slice(2).trim());
          }
          // Lines without a valid prefix are ignored
        }

        if (inputLines.length > 0 && outputLines.length > 0) {
          newTestCases.push({
            input: inputLines.join("\n"),
            output: outputLines.join("\n"),
            isHidden: index > 0, // First is public, rest are hidden
            order: index + 1,
          });
        }
      });

      if (newTestCases.length > 0) {
        setFormData(prev => ({ ...prev, testCases: newTestCases }));
        setErrors(prev => ({ ...prev, testCases: "" }));
      } else {
        setErrors(prev => ({ ...prev, testCases: "Could not parse any test cases. Ensure lines use I: and O: prefixes." }));
      }
    };
    reader.readAsText(file);
  };

  return (
    <div className="max-w-4xl mx-auto pb-12">
      <div className="mb-6 flex items-center gap-4">
        <Link href="/admin/problems" className="text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-6 h-6" />
        </Link>
        <h1 className="text-3xl font-bold text-white">Add New Problem</h1>
      </div>

      <div className="bg-[#1a1f29] rounded-[15px] border border-[#2d3748] p-8">
        <form onSubmit={handleSubmit} className="space-y-6">
          {errors.submit && (
            <div className="bg-red-500/10 border border-red-500 text-red-500 p-4 rounded-md">
              {errors.submit}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-gray-300 mb-2">Problem Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full bg-[#0f1419] border border-[#4a5568] rounded-md p-3 text-white focus:outline-none focus:border-[#00d4aa]"
                placeholder="e.g., Two Sum"
              />
              {errors.name && <p className="text-red-500 text-sm mt-1">{errors.name}</p>}
            </div>
            
            <div>
              <label className="block text-gray-300 mb-2">Short Code</label>
              <input
                type="text"
                value={formData.shortCode}
                onChange={(e) => setFormData({ ...formData, shortCode: e.target.value })}
                className="w-full bg-[#0f1419] border border-[#4a5568] rounded-md p-3 text-white focus:outline-none focus:border-[#00d4aa]"
                placeholder="e.g., TWO_SUM"
              />
              {errors.shortCode && <p className="text-red-500 text-sm mt-1">{errors.shortCode}</p>}
            </div>
          </div>

          <div>
            <label className="block text-gray-300 mb-2">Difficulty</label>
            <select
              value={formData.difficulty}
              onChange={(e) => setFormData({ ...formData, difficulty: e.target.value as any })}
              className="w-full bg-[#0f1419] border border-[#4a5568] rounded-md p-3 text-white focus:outline-none focus:border-[#00d4aa]"
            >
              <option value="E">Easy</option>
              <option value="M">Medium</option>
              <option value="H">Hard</option>
            </select>
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-gray-300">Problem Statement (Markdown)</label>
              <button
                type="button"
                onClick={() => setPreviewMode((v) => !v)}
                className="flex items-center gap-1.5 text-xs px-3 py-1 rounded border border-[#4a5568] text-gray-300 hover:border-[#00d4aa] hover:text-[#00d4aa] transition-colors"
              >
                {previewMode ? (
                  <><Edit3 className="w-3.5 h-3.5" /> Edit</>
                ) : (
                  <><Eye className="w-3.5 h-3.5" /> Preview</>
                )}
              </button>
            </div>
            {previewMode ? (
              <div className="w-full min-h-[240px] bg-[#0f1419] border border-[#4a5568] rounded-md p-4 prose prose-invert prose-sm max-w-none">
                {formData.statement ? (
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{formData.statement}</ReactMarkdown>
                ) : (
                  <p className="text-gray-600 italic">Nothing to preview yet. Switch to Edit and write your statement.</p>
                )}
              </div>
            ) : (
              <textarea
                value={formData.statement}
                onChange={(e) => setFormData({ ...formData, statement: e.target.value })}
                rows={10}
                className="w-full bg-[#0f1419] border border-[#4a5568] rounded-md p-3 text-white focus:outline-none focus:border-[#00d4aa] font-mono text-sm"
                placeholder="Write the problem description here..."
              />
            )}
            {errors.statement && <p className="text-red-500 text-sm mt-1">{errors.statement}</p>}
          </div>

          <div className="border-t border-[#4a5568] pt-8 mt-8">
            <div className="mb-4">
              <h3 className="text-xl font-bold text-white mb-2">Upload Test Cases (.txt)</h3>
              <div className="bg-[#0f1419] border border-[#4a5568] rounded-md p-4 mb-4 text-sm">
                <p className="text-gray-300 font-semibold mb-2">File Format:</p>
                <p className="text-gray-400 mb-1">• Each line must start with <code className="text-[#00d4aa]">I:</code> (input) or <code className="text-[#00d4aa]">O:</code> (output)</p>
                <p className="text-gray-400 mb-1">• Separate test cases with <strong className="text-white">one blank line</strong></p>
                <p className="text-gray-400 mb-3">• Multiple <code className="text-[#00d4aa]">I:</code> lines form multi-line input</p>
                <p className="text-gray-500 text-xs font-mono bg-[#1a1f29] p-3 rounded border border-[#2d3748] whitespace-pre">{`I:1 2\nO:3\n\nI:4 5\nO:9`}</p>
                <p className="text-[#00d4aa] text-xs mt-2">Note: The first test case is Public (visible to users), all others are Hidden.</p>
              </div>
              <input
                type="file"
                accept=".txt"
                onChange={handleFileUpload}
                className="block w-full text-sm text-gray-300
                  file:mr-4 file:py-2 file:px-4
                  file:rounded-md file:border-0
                  file:text-sm file:font-semibold
                  file:bg-[#00d4aa] file:text-[#0f1419]
                  hover:file:bg-[#00b38f] file:cursor-pointer cursor-pointer"
              />
            </div>
            
            {errors.testCases && <p className="text-red-500 text-sm mb-4">{errors.testCases}</p>}

            {formData.testCases.length > 0 && (
              <div className="bg-[#0f1419] p-4 rounded-md border border-[#4a5568] mt-4">
                <h4 className="text-[#00d4aa] font-bold mb-2">Parsed Successfully: {formData.testCases.length} Test Cases</h4>
                <div className="text-sm text-gray-300">
                  <p>1 Public Test Case, {formData.testCases.length - 1} Hidden Test Cases.</p>
                  <p className="mt-4 text-xs text-gray-500 uppercase tracking-wider font-bold">Preview of Test Case 1 (Public):</p>
                  <div className="grid grid-cols-2 gap-4 mt-2">
                    <div className="bg-[#1a1f29] p-3 rounded whitespace-pre-wrap font-mono text-sm border border-[#2d3748]">
                      <span className="text-[#a0aec0] block mb-2 border-b border-[#2d3748] pb-1 font-sans text-xs uppercase">Input</span>
                      {formData.testCases[0].input}
                    </div>
                    <div className="bg-[#1a1f29] p-3 rounded whitespace-pre-wrap font-mono text-sm border border-[#2d3748]">
                      <span className="text-[#a0aec0] block mb-2 border-b border-[#2d3748] pb-1 font-sans text-xs uppercase">Output</span>
                      {formData.testCases[0].output}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="flex justify-end pt-6">
            <button
              type="submit"
              disabled={mutation.isPending}
              className="btn btn-primary px-8 flex items-center gap-2"
            >
              <Save className="w-5 h-5" />
              {mutation.isPending ? "Saving..." : "Save Problem"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
