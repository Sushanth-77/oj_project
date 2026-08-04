"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, BookOpen, CheckCircle, Circle, TrendingUp, Lock } from "lucide-react";
import { useSession } from "next-auth/react";

const DIFF_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  E: { label: "Easy",   color: "text-green-400",  bg: "bg-green-400/20 border-green-400/30" },
  M: { label: "Medium", color: "text-yellow-400", bg: "bg-yellow-400/20 border-yellow-400/30" },
  H: { label: "Hard",   color: "text-red-400",    bg: "bg-red-400/20 border-red-400/30" },
};

export default function CollectionDetailPage() {
  const params = useParams();
  const slug = params.slug as string;
  const { data: session } = useSession();

  const { data: collection, isLoading, isError } = useQuery({
    queryKey: ["collection", slug],
    queryFn: async () => {
      const res = await fetch(`/api/collections/${slug}`);
      if (!res.ok) throw new Error("Not found");
      return res.json();
    },
  });

  if (isLoading) {
    return <div className="p-8 text-center text-gray-400">Loading collection...</div>;
  }
  if (isError || !collection) {
    return <div className="p-8 text-center text-red-400">Collection not found.</div>;
  }

  const problems = collection.problems || [];
  const solvedCount = problems.filter((cp: any) => cp.solved).length;
  const progress = problems.length > 0 ? Math.round((solvedCount / problems.length) * 100) : 0;

  return (
    <div className="min-h-screen bg-[#0f1419]">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Back */}
        <Link href="/collections" className="inline-flex items-center gap-2 text-[#00d4aa] text-sm mb-6 hover:text-[#00b38f]">
          <ArrowLeft className="w-4 h-4" />
          Back to Collections
        </Link>

        {/* Header */}
        <div className="bg-[#1a1f29] border border-[#2d3748] rounded-2xl p-6 mb-6">
          <div className="flex items-start gap-4 mb-4">
            <div className="p-3 bg-[#00d4aa]/10 rounded-xl">
              <BookOpen className="w-6 h-6 text-[#00d4aa]" />
            </div>
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-white mb-1">{collection.title}</h1>
              {collection.description && (
                <p className="text-gray-400 text-sm">{collection.description}</p>
              )}
            </div>
          </div>

          {/* Progress bar */}
          {session && (
            <div className="mt-4 pt-4 border-t border-[#2d3748]">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-400">Your Progress</span>
                <span className="text-sm font-semibold text-[#00d4aa]">{solvedCount}/{problems.length} solved</span>
              </div>
              <div className="w-full h-2 bg-[#2d3748] rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-[#00d4aa] to-[#00b894] rounded-full transition-all duration-700"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="text-xs text-gray-600 mt-1">{progress}% complete</p>
            </div>
          )}
        </div>

        {/* Problem list */}
        <div className="space-y-2">
          {problems.map((cp: any, idx: number) => {
            const d = DIFF_CONFIG[cp.problem.difficulty] || DIFF_CONFIG["E"];
            return (
              <div
                key={cp.id}
                className={`bg-[#1a1f29] border rounded-xl px-5 py-4 flex items-center gap-4 hover:border-[#00d4aa]/30 transition-all group ${
                  cp.solved ? "border-green-400/20" : "border-[#2d3748]"
                }`}
              >
                <span className="text-gray-600 font-mono text-sm w-6 flex-shrink-0">{idx + 1}</span>

                {session ? (
                  cp.solved ? (
                    <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
                  ) : (
                    <Circle className="w-5 h-5 text-gray-600 flex-shrink-0" />
                  )
                ) : null}

                <Link
                  href={`/problems/${cp.problem.shortCode}`}
                  className="flex-1 text-white font-semibold hover:text-[#00d4aa] transition-colors group-hover:text-[#00d4aa] truncate"
                >
                  {cp.problem.name}
                </Link>

                <div className="flex items-center gap-2 flex-shrink-0">
                  {cp.problem.topics.slice(0, 2).map((t: string) => (
                    <span key={t} className="text-xs px-2 py-0.5 rounded-full bg-[#00d4aa]/10 text-[#00d4aa] border border-[#00d4aa]/20 hidden sm:inline-block">
                      {t}
                    </span>
                  ))}
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${d.bg} ${d.color}`}>
                    {d.label}
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {problems.length === 0 && (
          <div className="text-center py-16 text-gray-500">
            <BookOpen className="w-10 h-10 mx-auto mb-2 opacity-30" />
            No problems in this collection yet.
          </div>
        )}
      </div>
    </div>
  );
}
