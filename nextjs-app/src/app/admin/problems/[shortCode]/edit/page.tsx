"use client";

import { useState, useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter, useParams } from "next/navigation";
import { PlusCircle, Trash2, Save, ArrowLeft, BookOpen, Calendar } from "lucide-react";
import Link from "next/link";
import { z } from "zod";
import { createProblemSchema } from "@/lib/validations";
import { Problem, TestCase } from "@/types";

type ProblemFormData = z.infer<typeof createProblemSchema>;

export default function AdminEditProblem() {
  const router = useRouter();
  const params = useParams();
  const shortCode = params.shortCode as string;
  const queryClient = useQueryClient();

  const [formData, setFormData] = useState<ProblemFormData>({
    name: "",
    shortCode: "",
    statement: "",
    difficulty: "E",
    testCases: [{ input: "", output: "", isHidden: false, order: 1 }],
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [editorial, setEditorial] = useState("");
  const [editorialCode, setEditorialCode] = useState("");
  const [isDailyChallenge, setIsDailyChallenge] = useState(false);
  const [templates, setTemplates] = useState({ python: "", cpp: "", c: "", java: "", javascript: "" });
  const [showTemplates, setShowTemplates] = useState(false);
  const [showEditorial, setShowEditorial] = useState(false);

  const { data: problem, isLoading } = useQuery<Problem>({
    queryKey: ["adminProblem", shortCode],
    queryFn: async () => {
      const res = await fetch(`/api/problems/${shortCode}`);
      if (!res.ok) throw new Error("Failed to fetch problem");
      return res.json();
    },
  });

  useEffect(() => {
    if (problem) {
      setFormData({
        name: problem.name,
        shortCode: problem.shortCode,
        statement: problem.statement,
        difficulty: problem.difficulty,
        testCases: problem.testCases && problem.testCases.length > 0 
          ? problem.testCases.map((tc: TestCase) => ({
              input: tc.input,
              output: tc.output,
              isHidden: tc.isHidden,
              order: tc.order
            }))
          : [{ input: "", output: "", isHidden: false, order: 1 }],
      });
      // Load optional fields
      const tmpl = (problem as any).templates as Record<string, string> | null;
      if (tmpl) {
        setTemplates({
          python: tmpl.python || "",
          cpp: tmpl.cpp || "",
          c: tmpl.c || "",
          java: tmpl.java || "",
          javascript: tmpl.javascript || "",
        });
      }
      setEditorial((problem as any).editorial || "");
      setEditorialCode((problem as any).editorialCode || "");
      setIsDailyChallenge(!!(problem as any).isDailyChallenge);
    }
  }, [problem]);

  const mutation = useMutation({
    mutationFn: async (data: ProblemFormData) => {
      if (!problem) throw new Error("Problem not loaded");

      // Build templates object (only include non-empty ones)
      const tmpl: Record<string, string> = {};
      if (templates.python.trim()) tmpl.python = templates.python;
      if (templates.cpp.trim()) tmpl.cpp = templates.cpp;
      if (templates.c.trim()) tmpl.c = templates.c;
      if (templates.java.trim()) tmpl.java = templates.java;
      if (templates.javascript.trim()) tmpl.javascript = templates.javascript;

      const res = await fetch(`/api/admin/problems?id=${problem.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...data,
          templates: Object.keys(tmpl).length > 0 ? tmpl : null,
          editorial: editorial.trim() || null,
          editorialCode: editorialCode.trim() || null,
          isDailyChallenge,
        }),
      });
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.error || "Failed to update problem");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["adminProblems"] });
      queryClient.invalidateQueries({ queryKey: ["problem", shortCode] });
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

  const addTestCase = () => {
    setFormData({
      ...formData,
      testCases: [
        ...formData.testCases,
        { input: "", output: "", isHidden: false, order: formData.testCases.length + 1 },
      ],
    });
  };

  const removeTestCase = (index: number) => {
    const newTestCases = [...formData.testCases];
    newTestCases.splice(index, 1);
    setFormData({ ...formData, testCases: newTestCases });
  };

  const updateTestCase = (index: number, field: string, value: any) => {
    const newTestCases = [...formData.testCases];
    newTestCases[index] = { ...newTestCases[index], [field]: value };
    setFormData({ ...formData, testCases: newTestCases });
  };

  if (isLoading) {
    return <div className="text-white p-8">Loading problem...</div>;
  }

  return (
    <div className="max-w-4xl mx-auto pb-12">
      <div className="mb-6 flex items-center gap-4">
        <Link href="/admin/problems" className="text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-6 h-6" />
        </Link>
        <h1 className="text-3xl font-bold text-white">Edit Problem: {problem?.name}</h1>
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
              />
              {errors.shortCode && <p className="text-red-500 text-sm mt-1">{errors.shortCode}</p>}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-6">
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

            {/* Daily Challenge Toggle */}
            <div>
              <label className="block text-gray-300 mb-2">Daily Challenge</label>
              <label className="flex items-center gap-3 mt-3 cursor-pointer">
                <div
                  onClick={() => setIsDailyChallenge((v) => !v)}
                  className={`w-12 h-6 rounded-full transition-colors relative ${
                    isDailyChallenge ? "bg-[#00d4aa]" : "bg-[#2d3748]"
                  }`}
                >
                  <span className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-all ${
                    isDailyChallenge ? "left-7" : "left-1"
                  }`} />
                </div>
                <div className="flex items-center gap-1.5 text-gray-300 text-sm">
                  <Calendar className="w-4 h-4 text-[#00d4aa]" />
                  {isDailyChallenge ? "Set as today's challenge" : "Not a daily challenge"}
                </div>
              </label>
            </div>
          </div>

          <div>
            <label className="block text-gray-300 mb-2">Problem Statement (Markdown)</label>
            <textarea
              value={formData.statement}
              onChange={(e) => setFormData({ ...formData, statement: e.target.value })}
              rows={10}
              className="w-full bg-[#0f1419] border border-[#4a5568] rounded-md p-3 text-white focus:outline-none focus:border-[#00d4aa] font-mono text-sm"
            />
            {errors.statement && <p className="text-red-500 text-sm mt-1">{errors.statement}</p>}
          </div>

          {/* Code Templates */}
          <div className="border border-[#2d3748] rounded-lg overflow-hidden">
            <button
              type="button"
              onClick={() => setShowTemplates(!showTemplates)}
              className="w-full flex items-center justify-between px-4 py-3 bg-[#0f1419] text-sm text-gray-400 hover:text-white transition-colors"
            >
              <span className="font-medium">⌨️ Code Templates (optional)</span>
              <span className="text-xs text-gray-600">{showTemplates ? "▲ Hide" : "▼ Show"}</span>
            </button>
            {showTemplates && (
              <div className="p-4 space-y-4">
                <p className="text-xs text-gray-500">Override the default boilerplate for this problem.</p>
                {(["python", "cpp", "c", "java", "javascript"] as const).map((lang) => (
                  <div key={lang}>
                    <label className="block text-gray-400 text-xs font-semibold uppercase mb-1">
                      {lang === "python" ? "Python 3" : lang === "cpp" ? "C++" : lang === "java" ? "Java" : lang === "javascript" ? "JavaScript" : "C"}
                    </label>
                    <textarea
                      value={templates[lang]}
                      onChange={(e) => setTemplates((prev) => ({ ...prev, [lang]: e.target.value }))}
                      placeholder={`Default ${lang} boilerplate…`}
                      rows={4}
                      className="w-full bg-[#0f1419] border border-[#4a5568] rounded-md p-3 text-sm text-gray-200 font-mono focus:outline-none focus:border-[#00d4aa] placeholder-gray-700"
                    />
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Editorial */}
          <div className="border border-[#2d3748] rounded-lg overflow-hidden">
            <button
              type="button"
              onClick={() => setShowEditorial(!showEditorial)}
              className="w-full flex items-center justify-between px-4 py-3 bg-[#0f1419] text-sm text-gray-400 hover:text-white transition-colors"
            >
              <span className="font-medium flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-[#00d4aa]" />
                Editorial (optional — unlocked after solving or 3 attempts)
              </span>
              <span className="text-xs text-gray-600">{showEditorial ? "▲ Hide" : "▼ Show"}</span>
            </button>
            {showEditorial && (
              <div className="p-4 space-y-4">
                <div>
                  <label className="block text-gray-400 text-xs font-semibold uppercase mb-1">Editorial Body (Markdown)</label>
                  <textarea
                    value={editorial}
                    onChange={(e) => setEditorial(e.target.value)}
                    placeholder="Explain the approach, intuition, and time/space complexity…"
                    rows={8}
                    className="w-full bg-[#0f1419] border border-[#4a5568] rounded-md p-3 text-sm text-gray-200 font-mono focus:outline-none focus:border-[#00d4aa] placeholder-gray-700"
                  />
                </div>
                <div>
                  <label className="block text-gray-400 text-xs font-semibold uppercase mb-1">Reference Solution Code</label>
                  <textarea
                    value={editorialCode}
                    onChange={(e) => setEditorialCode(e.target.value)}
                    placeholder="Paste the reference implementation here…"
                    rows={8}
                    className="w-full bg-[#0f1419] border border-[#4a5568] rounded-md p-3 text-sm text-gray-200 font-mono focus:outline-none focus:border-[#00d4aa] placeholder-gray-700"
                  />
                </div>
              </div>
            )}
          </div>

          {/* Test Cases */}
          <div className="border-t border-[#4a5568] pt-8 mt-8">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold text-white">Test Cases</h3>
              <button
                type="button"
                onClick={addTestCase}
                className="btn btn-secondary text-sm flex items-center gap-2"
              >
                <PlusCircle className="w-4 h-4" /> Add Test Case
              </button>
            </div>
            
            {errors.testCases && <p className="text-red-500 text-sm mb-4">{errors.testCases}</p>}

            <div className="space-y-4">
              {formData.testCases.map((tc, index) => (
                <div key={index} className="bg-[#0f1419] p-4 rounded-md border border-[#4a5568] relative">
                  <button
                    type="button"
                    onClick={() => removeTestCase(index)}
                    className="absolute top-4 right-4 text-red-500 hover:text-red-400"
                    disabled={formData.testCases.length === 1}
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div>
                      <label className="block text-gray-400 text-sm mb-1">Input</label>
                      <textarea
                        value={tc.input}
                        onChange={(e) => updateTestCase(index, "input", e.target.value)}
                        rows={3}
                        className="w-full bg-[#1a1f29] border border-[#2d3748] rounded p-2 text-gray-300 font-mono text-sm"
                      />
                    </div>
                    <div>
                      <label className="block text-gray-400 text-sm mb-1">Expected Output</label>
                      <textarea
                        value={tc.output}
                        onChange={(e) => updateTestCase(index, "output", e.target.value)}
                        rows={3}
                        className="w-full bg-[#1a1f29] border border-[#2d3748] rounded p-2 text-gray-300 font-mono text-sm"
                      />
                      {errors[`testCases.${index}.output`] && <p className="text-red-500 text-xs mt-1">{errors[`testCases.${index}.output`]}</p>}
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id={`hidden-${index}`}
                      checked={tc.isHidden}
                      onChange={(e) => updateTestCase(index, "isHidden", e.target.checked)}
                      className="rounded bg-[#1a1f29] border-[#4a5568]"
                    />
                    <label htmlFor={`hidden-${index}`} className="text-gray-400 text-sm">
                      Hidden Test Case (not shown to users)
                    </label>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="flex justify-end pt-6">
            <button
              type="submit"
              disabled={mutation.isPending}
              className="btn btn-primary px-8 flex items-center gap-2"
            >
              <Save className="w-5 h-5" />
              {mutation.isPending ? "Saving..." : "Update Problem"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
