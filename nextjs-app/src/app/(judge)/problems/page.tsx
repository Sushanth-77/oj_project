"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState, useMemo } from "react";
import { Search, ChevronRight, X, CheckCircle2, Tag } from "lucide-react";
import { useSession } from "next-auth/react";
import { Problem } from "@/types";

type DifficultyFilter = "ALL" | "E" | "M" | "H";

const DIFFICULTY_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  E: { label: "Easy",   color: "text-green-400",  bg: "bg-green-400/10 border border-green-400/30" },
  M: { label: "Medium", color: "text-yellow-400", bg: "bg-yellow-400/10 border border-yellow-400/30" },
  H: { label: "Hard",   color: "text-red-400",    bg: "bg-red-400/10 border border-red-400/30" },
};

export default function ProblemsPage() {
  const [search, setSearch] = useState("");
  const [difficultyFilter, setDifficultyFilter] = useState<DifficultyFilter>("ALL");
  const [selectedTopics, setSelectedTopics] = useState<string[]>([]);
  const { data: session } = useSession();

  const isNumberSearch = search.startsWith("#");
  const apiSearch = isNumberSearch ? "" : search;
  const searchNumber = isNumberSearch ? parseInt(search.slice(1)) : null;

  // Fetch problems
  const { data: problems, isLoading, isError, refetch } = useQuery<Problem[]>({
    queryKey: ["problems", apiSearch],
    queryFn: async () => {
      const url = apiSearch ? `/api/problems?search=${encodeURIComponent(apiSearch)}` : "/api/problems";
      const res = await fetch(url);
      if (!res.ok) throw new Error("Failed to fetch problems");
      return res.json();
    },
  });

  // Fetch solved problem IDs (only when logged in)
  const { data: solvedData } = useQuery<{ solvedProblemIds: number[] }>({
    queryKey: ["solvedProblems"],
    queryFn: async () => {
      const res = await fetch("/api/problems/solved");
      if (!res.ok) return { solvedProblemIds: [] };
      return res.json();
    },
    enabled: !!session,
    staleTime: 30_000,
  });

  const solvedSet = useMemo(
    () => new Set(solvedData?.solvedProblemIds ?? []),
    [solvedData]
  );

  // Derive all unique topics from loaded problems
  const allTopics = useMemo(() => {
    const set = new Set<string>();
    problems?.forEach((p) => p.topics?.forEach((t) => set.add(t)));
    return Array.from(set).sort();
  }, [problems]);

  const toggleTopic = (topic: string) => {
    setSelectedTopics((prev) =>
      prev.includes(topic) ? prev.filter((t) => t !== topic) : [...prev, topic]
    );
  };

  const filtered = problems?.filter((p, index) => {
    const passesDifficulty = difficultyFilter === "ALL" || p.difficulty === difficultyFilter;
    const passesNumber =
      !isNumberSearch ||
      (searchNumber !== null && !isNaN(searchNumber) && index + 1 === searchNumber);
    const passesTopics =
      selectedTopics.length === 0 ||
      selectedTopics.some((t) => p.topics?.includes(t));
    return passesDifficulty && passesNumber && passesTopics;
  }) ?? [];

  const counts = {
    ALL: problems?.length ?? 0,
    E:   problems?.filter((p) => p.difficulty === "E").length ?? 0,
    M:   problems?.filter((p) => p.difficulty === "M").length ?? 0,
    H:   problems?.filter((p) => p.difficulty === "H").length ?? 0,
  };

  const solvedCounts = {
    E: problems?.filter((p) => p.difficulty === "E" && solvedSet.has(p.id)).length ?? 0,
    M: problems?.filter((p) => p.difficulty === "M" && solvedSet.has(p.id)).length ?? 0,
    H: problems?.filter((p) => p.difficulty === "H" && solvedSet.has(p.id)).length ?? 0,
  };

  return (
    <div className="min-h-screen bg-[#0f1419]">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">

        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Problems</h1>
          <p className="text-gray-400">Solve challenges, improve your skills.</p>
        </div>

        {/* Progress cards (only when logged in) */}
        {session && !search && (
          <div className="grid grid-cols-3 gap-4 mb-8">
            {(["E", "M", "H"] as const).map((d) => {
              const cfg = DIFFICULTY_CONFIG[d];
              const solved = solvedCounts[d];
              const total = counts[d];
              const pct = total > 0 ? Math.round((solved / total) * 100) : 0;
              return (
                <div key={d} className="bg-[#1a1f29] rounded-xl border border-[#2d3748] p-4">
                  <div className="flex justify-between items-center mb-2">
                    <span className={`text-sm font-semibold ${cfg.color}`}>{cfg.label}</span>
                    <span className="text-xs text-gray-500">{solved} / {total}</span>
                  </div>
                  <div className="w-full bg-[#2d3748] rounded-full h-1.5">
                    <div
                      className={`h-1.5 rounded-full transition-all duration-500 ${
                        d === "E" ? "bg-green-400" : d === "M" ? "bg-yellow-400" : "bg-red-400"
                      }`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Search Bar */}
        <div className="relative mb-5">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by name, code, or #number..."
            className="w-full bg-[#1a1f29] border border-[#2d3748] rounded-lg pl-10 pr-10 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-[#00d4aa] transition-colors"
          />
          {search && (
            <button
              onClick={() => setSearch("")}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        {/* Difficulty Filter Tabs */}
        <div className="flex gap-2 mb-4 flex-wrap">
          {(["ALL", "E", "M", "H"] as DifficultyFilter[]).map((d) => {
            const isActive = difficultyFilter === d;
            const label = d === "ALL" ? "All" : DIFFICULTY_CONFIG[d].label;
            return (
              <button
                key={d}
                onClick={() => setDifficultyFilter(d)}
                className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all border ${
                  isActive
                    ? d === "ALL" ? "bg-[#00d4aa] text-[#0f1419] border-[#00d4aa]"
                      : d === "E" ? "bg-green-400 text-[#0f1419] border-green-400"
                      : d === "M" ? "bg-yellow-400 text-[#0f1419] border-yellow-400"
                      : "bg-red-400 text-[#0f1419] border-red-400"
                    : "bg-transparent text-gray-400 border-[#2d3748] hover:border-gray-500 hover:text-gray-200"
                }`}
              >
                {label} <span className="ml-1 opacity-60">({counts[d]})</span>
              </button>
            );
          })}
        </div>

        {/* Topic Filter */}
        {allTopics.length > 0 && (
          <div className="mb-6">
            <div className="flex items-center gap-2 mb-2">
              <Tag className="h-3.5 w-3.5 text-gray-500" />
              <span className="text-xs text-gray-500 uppercase tracking-wider font-semibold">Topics</span>
              {selectedTopics.length > 0 && (
                <button
                  onClick={() => setSelectedTopics([])}
                  className="text-xs text-[#00d4aa] hover:underline ml-1"
                >
                  Clear
                </button>
              )}
            </div>
            <div className="flex flex-wrap gap-2">
              {allTopics.map((topic) => {
                const isActive = selectedTopics.includes(topic);
                return (
                  <button
                    key={topic}
                    onClick={() => toggleTopic(topic)}
                    className={`px-3 py-1 rounded-full text-xs font-medium transition-all border ${
                      isActive
                        ? "bg-[#00d4aa]/20 text-[#00d4aa] border-[#00d4aa]/60"
                        : "bg-transparent text-gray-400 border-[#2d3748] hover:border-gray-500 hover:text-gray-300"
                    }`}
                  >
                    {topic}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Problems Table */}
        <div className="bg-[#1a1f29] rounded-xl border border-[#2d3748] overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-[#2d3748]">
                <th className="text-left p-4 text-xs font-semibold text-gray-500 uppercase tracking-wider w-10">#</th>
                <th className="text-left p-4 text-xs font-semibold text-gray-500 uppercase tracking-wider w-8" />
                <th className="text-left p-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Title</th>
                <th className="text-left p-4 text-xs font-semibold text-gray-500 uppercase tracking-wider hidden sm:table-cell">Code</th>
                <th className="text-left p-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Difficulty</th>
                <th className="w-10" />
              </tr>
            </thead>
            <tbody className="divide-y divide-[#2d3748]">
              {isLoading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    <td className="p-4"><div className="h-4 w-6 bg-[#2d3748] rounded" /></td>
                    <td className="p-4"><div className="h-4 w-4 bg-[#2d3748] rounded-full" /></td>
                    <td className="p-4"><div className="h-4 w-48 bg-[#2d3748] rounded" /></td>
                    <td className="p-4 hidden sm:table-cell"><div className="h-4 w-20 bg-[#2d3748] rounded" /></td>
                    <td className="p-4"><div className="h-4 w-14 bg-[#2d3748] rounded" /></td>
                    <td className="p-4" />
                  </tr>
                ))
              ) : isError ? (
                <tr>
                  <td colSpan={6} className="p-10 text-center">
                    <p className="text-red-400 mb-3">Failed to load problems.</p>
                    <button onClick={() => refetch()} className="text-sm text-[#00d4aa] hover:underline">Retry</button>
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-10 text-center text-gray-500">
                    {search ? `No problems found matching "${search}".` : "No problems available yet."}
                  </td>
                </tr>
              ) : (
                filtered.map((problem, index) => {
                  const diff = DIFFICULTY_CONFIG[problem.difficulty];
                  const isSolved = solvedSet.has(problem.id);
                  return (
                    <tr key={problem.id} className="hover:bg-white/5 transition-colors group">
                      <td className="p-4 text-gray-600 text-sm font-mono">{index + 1}</td>
                      {/* Solved indicator */}
                      <td className="p-4">
                        {isSolved ? (
                          <span title="Solved">
                            <CheckCircle2 className="w-4 h-4 text-green-400" />
                          </span>
                        ) : (
                          <div className="w-4 h-4" />
                        )}
                      </td>
                      <td className="p-4">
                        <div className="flex flex-col gap-1">
                          <Link
                            href={`/problems/${problem.shortCode}`}
                            className={`font-medium transition-colors group-hover:text-[#00d4aa] ${
                              isSolved ? "text-green-300" : "text-white"
                            }`}
                          >
                            {problem.name}
                            {isSolved && (
                              <span className="ml-2 text-[10px] font-bold tracking-widest uppercase bg-green-400/15 text-green-400 border border-green-400/30 px-1.5 py-0.5 rounded-full align-middle">
                                Solved
                              </span>
                            )}
                          </Link>
                          {/* Topic chips */}
                          {problem.topics && problem.topics.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-0.5">
                              {problem.topics.map((topic) => (
                                <button
                                  key={topic}
                                  onClick={() => {
                                    if (!selectedTopics.includes(topic)) {
                                      setSelectedTopics([topic]);
                                      window.scrollTo({ top: 0, behavior: "smooth" });
                                    }
                                  }}
                                  className={`text-[10px] px-2 py-0.5 rounded-full border transition-colors cursor-pointer ${
                                    selectedTopics.includes(topic)
                                      ? "bg-[#00d4aa]/20 text-[#00d4aa] border-[#00d4aa]/50"
                                      : "bg-[#2d3748]/50 text-gray-500 border-[#2d3748] hover:text-gray-300 hover:border-gray-500"
                                  }`}
                                >
                                  {topic}
                                </button>
                              ))}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="p-4 hidden sm:table-cell">
                        <span className="text-gray-500 font-mono text-xs">{problem.shortCode}</span>
                      </td>
                      <td className="p-4">
                        <span className={`inline-block px-2.5 py-1 rounded-full text-xs font-semibold ${diff.bg} ${diff.color}`}>
                          {diff.label}
                        </span>
                      </td>
                      <td className="p-4">
                        <ChevronRight className="w-4 h-4 text-gray-600 group-hover:text-[#00d4aa] transition-colors" />
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {!isLoading && !isError && filtered.length > 0 && (
          <p className="text-center text-gray-600 text-sm mt-4">
            Showing {filtered.length} problem{filtered.length !== 1 ? "s" : ""}
            {selectedTopics.length > 0 && ` · filtered by: ${selectedTopics.join(", ")}`}
          </p>
        )}
      </div>
    </div>
  );
}
