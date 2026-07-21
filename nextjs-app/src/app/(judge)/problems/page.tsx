"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";
import { Search, ChevronRight, X } from "lucide-react";
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
  const { data: session } = useSession();

  const isNumberSearch = search.startsWith("#");
  const apiSearch = isNumberSearch ? "" : search;
  const searchNumber = isNumberSearch ? parseInt(search.slice(1)) : null;

  const { data: problems, isLoading, isError, refetch } = useQuery<Problem[]>({
    queryKey: ["problems", apiSearch],
    queryFn: async () => {
      const url = apiSearch ? `/api/problems?search=${encodeURIComponent(apiSearch)}` : "/api/problems";
      const res = await fetch(url);
      if (!res.ok) throw new Error("Failed to fetch problems");
      return res.json();
    },
  });

  const filtered = problems?.filter((p, index) => {
    const passesDifficulty = difficultyFilter === "ALL" || p.difficulty === difficultyFilter;
    // #N search: filter client-side by 1-based row number
    const passesNumber = !isNumberSearch || (searchNumber !== null && !isNaN(searchNumber) && index + 1 === searchNumber);
    return passesDifficulty && passesNumber;
  }) ?? [];

  const counts = {
    ALL: problems?.length ?? 0,
    E:   problems?.filter((p) => p.difficulty === "E").length ?? 0,
    M:   problems?.filter((p) => p.difficulty === "M").length ?? 0,
    H:   problems?.filter((p) => p.difficulty === "H").length ?? 0,
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
            {(["E","M","H"] as const).map((d) => {
              const cfg = DIFFICULTY_CONFIG[d];
              return (
                <div key={d} className="bg-[#1a1f29] rounded-xl border border-[#2d3748] p-4">
                  <div className="flex justify-between items-center mb-2">
                    <span className={`text-sm font-semibold ${cfg.color}`}>{cfg.label}</span>
                    <span className="text-xs text-gray-500">0 / {counts[d]}</span>
                  </div>
                  <div className="w-full bg-[#2d3748] rounded-full h-1.5">
                    <div className={`h-1.5 rounded-full ${d === "E" ? "bg-green-400" : d === "M" ? "bg-yellow-400" : "bg-red-400"}`} style={{ width: "0%" }} />
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
        <div className="flex gap-2 mb-6 flex-wrap">
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

        {/* Problems Table */}
        <div className="bg-[#1a1f29] rounded-xl border border-[#2d3748] overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-[#2d3748]">
                <th className="text-left p-4 text-xs font-semibold text-gray-500 uppercase tracking-wider w-12">#</th>
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
                    <td className="p-4"><div className="h-4 w-48 bg-[#2d3748] rounded" /></td>
                    <td className="p-4 hidden sm:table-cell"><div className="h-4 w-20 bg-[#2d3748] rounded" /></td>
                    <td className="p-4"><div className="h-4 w-14 bg-[#2d3748] rounded" /></td>
                    <td className="p-4" />
                  </tr>
                ))
              ) : isError ? (
                <tr>
                  <td colSpan={5} className="p-10 text-center">
                    <p className="text-red-400 mb-3">Failed to load problems.</p>
                    <button onClick={() => refetch()} className="text-sm text-[#00d4aa] hover:underline">Retry</button>
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-10 text-center text-gray-500">
                    {search ? `No problems found matching "${search}".` : "No problems available yet."}
                  </td>
                </tr>
              ) : (
                filtered.map((problem, index) => {
                  const diff = DIFFICULTY_CONFIG[problem.difficulty];
                  return (
                    <tr key={problem.id} className="hover:bg-white/5 transition-colors group">
                      <td className="p-4 text-gray-600 text-sm font-mono">{index + 1}</td>
                      <td className="p-4">
                        <Link
                          href={`/problems/${problem.shortCode}`}
                          className="text-white font-medium group-hover:text-[#00d4aa] transition-colors"
                        >
                          {problem.name}
                        </Link>
                        <p className="text-gray-600 text-xs mt-0.5 line-clamp-1">
                          {problem.statement?.substring(0, 80)}...
                        </p>
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
          </p>
        )}
      </div>
    </div>
  );
}
