"use client";

import { useQuery } from "@tanstack/react-query";
import { useSession } from "next-auth/react";
import { useState } from "react";
import Link from "next/link";
import { Trophy, Medal, Crown, TrendingUp, Users, Zap } from "lucide-react";
import { LeaderboardEntry } from "@/types";

const DIFF_COLORS = {
  easy:   { color: "text-green-400",  bg: "bg-green-400/10 border-green-400/30" },
  medium: { color: "text-yellow-400", bg: "bg-yellow-400/10 border-yellow-400/30" },
  hard:   { color: "text-red-400",    bg: "bg-red-400/10 border-red-400/30" },
};

function RankBadge({ rank }: { rank: number }) {
  if (rank === 1) return <Crown className="w-6 h-6 text-yellow-400" />;
  if (rank === 2) return <Medal className="w-6 h-6 text-gray-300" />;
  if (rank === 3) return <Medal className="w-6 h-6 text-amber-600" />;
  return <span className="text-gray-500 font-mono text-sm w-6 text-center">{rank}</span>;
}

function Avatar({ name, image, size = 8 }: { name?: string | null; image?: string | null; size?: number }) {
  if (image) {
    return (
      <img
        src={image}
        alt={name ?? "user"}
        className={`w-${size} h-${size} rounded-full object-cover ring-2 ring-[#2d3748]`}
      />
    );
  }
  const initials = name ? name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2) : "?";
  return (
    <div className={`w-${size} h-${size} rounded-full bg-gradient-to-br from-[#00d4aa] to-[#00b894] flex items-center justify-center text-white font-bold text-sm`}>
      {initials}
    </div>
  );
}

export default function LeaderboardPage() {
  const [range, setRange] = useState<"all" | "week">("all");
  const { data: session } = useSession();

  const { data, isLoading, isError } = useQuery<{
    leaderboard: LeaderboardEntry[];
    currentUserRank: number | null;
    currentUserId: string | null;
  }>({
    queryKey: ["leaderboard", range],
    queryFn: async () => {
      const res = await fetch(`/api/leaderboard?range=${range}`);
      if (!res.ok) throw new Error("Failed to fetch leaderboard");
      return res.json();
    },
    staleTime: 30_000,
  });

  const leaderboard = data?.leaderboard ?? [];
  const top3 = leaderboard.slice(0, 3);
  const rest = leaderboard.slice(3);

  return (
    <div className="min-h-screen bg-[#0f1419]">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">

        {/* Header */}
        <div className="mb-8 text-center">
          <div className="inline-flex items-center gap-3 mb-3">
            <Trophy className="w-8 h-8 text-yellow-400" />
            <h1 className="text-4xl font-bold text-white">Leaderboard</h1>
          </div>
          <p className="text-gray-400">Ranked by difficulty-weighted score · Hard=3pts, Medium=2pts, Easy=1pt</p>
        </div>

        {/* Current user rank banner */}
        {session && data?.currentUserRank && (
          <div className="mb-6 bg-[#00d4aa]/10 border border-[#00d4aa]/30 rounded-xl p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <TrendingUp className="w-5 h-5 text-[#00d4aa]" />
              <span className="text-[#00d4aa] font-semibold">Your rank</span>
            </div>
            <span className="text-white text-2xl font-bold">#{data.currentUserRank}</span>
          </div>
        )}

        {/* Range switcher */}
        <div className="flex gap-2 mb-8 justify-center">
          {(["all", "week"] as const).map((r) => (
            <button
              key={r}
              onClick={() => setRange(r)}
              className={`px-6 py-2 rounded-full text-sm font-semibold transition-all border ${
                range === r
                  ? "bg-[#00d4aa] text-[#0f1419] border-[#00d4aa]"
                  : "bg-transparent text-gray-400 border-[#2d3748] hover:border-gray-500 hover:text-gray-200"
              }`}
            >
              {r === "all" ? "All Time" : "This Week"}
            </button>
          ))}
        </div>

        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="h-16 bg-[#1a1f29] rounded-xl animate-pulse" />
            ))}
          </div>
        ) : isError ? (
          <div className="text-center py-16 text-red-400">Failed to load leaderboard.</div>
        ) : leaderboard.length === 0 ? (
          <div className="text-center py-16">
            <Users className="w-12 h-12 text-gray-600 mx-auto mb-3" />
            <p className="text-gray-400">No submissions yet for this period.</p>
          </div>
        ) : (
          <>
            {/* Podium for top 3 */}
            {top3.length >= 1 && (
              <div className="grid grid-cols-3 gap-3 mb-8">
                {/* 2nd place */}
                {top3[1] ? (
                  <div className="flex flex-col items-center pt-6">
                    <Avatar name={top3[1].name} image={top3[1].image} size={12} />
                    <Medal className="w-6 h-6 text-gray-300 mt-2 mb-1" />
                    <p className="text-white font-semibold text-sm text-center truncate w-full px-2">
                      {top3[1].name || top3[1].email.split("@")[0]}
                    </p>
                    <p className="text-gray-400 text-xs">{top3[1].score} pts</p>
                    <div className="bg-[#2d3748] w-full mt-3 rounded-t-lg h-16 flex items-center justify-center">
                      <span className="text-gray-300 font-bold text-xl">2</span>
                    </div>
                  </div>
                ) : <div />}

                {/* 1st place */}
                <div className="flex flex-col items-center">
                  <div className="relative">
                    <Avatar name={top3[0].name} image={top3[0].image} size={16} />
                    <Crown className="w-7 h-7 text-yellow-400 absolute -top-4 left-1/2 -translate-x-1/2" />
                  </div>
                  <p className="text-white font-bold text-sm text-center mt-2 truncate w-full px-2">
                    {top3[0].name || top3[0].email.split("@")[0]}
                  </p>
                  <p className="text-yellow-400 text-xs font-semibold">{top3[0].score} pts</p>
                  <div className="bg-gradient-to-b from-yellow-400/20 to-yellow-400/5 border border-yellow-400/30 w-full mt-3 rounded-t-lg h-24 flex items-center justify-center">
                    <span className="text-yellow-400 font-bold text-2xl">1</span>
                  </div>
                </div>

                {/* 3rd place */}
                {top3[2] ? (
                  <div className="flex flex-col items-center pt-10">
                    <Avatar name={top3[2].name} image={top3[2].image} size={10} />
                    <Medal className="w-5 h-5 text-amber-600 mt-2 mb-1" />
                    <p className="text-white font-semibold text-sm text-center truncate w-full px-2">
                      {top3[2].name || top3[2].email.split("@")[0]}
                    </p>
                    <p className="text-gray-400 text-xs">{top3[2].score} pts</p>
                    <div className="bg-[#2d3748]/70 w-full mt-3 rounded-t-lg h-10 flex items-center justify-center">
                      <span className="text-amber-600 font-bold text-lg">3</span>
                    </div>
                  </div>
                ) : <div />}
              </div>
            )}

            {/* Full ranked table */}
            <div className="bg-[#1a1f29] rounded-xl border border-[#2d3748] overflow-hidden">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-[#2d3748]">
                    <th className="text-left p-4 text-xs font-semibold text-gray-500 uppercase tracking-wider w-12">Rank</th>
                    <th className="text-left p-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">User</th>
                    <th className="text-center p-4 text-xs font-semibold text-gray-500 uppercase tracking-wider hidden sm:table-cell">Solved</th>
                    <th className="text-center p-4 text-xs font-semibold text-green-500/70 uppercase tracking-wider hidden md:table-cell">E</th>
                    <th className="text-center p-4 text-xs font-semibold text-yellow-500/70 uppercase tracking-wider hidden md:table-cell">M</th>
                    <th className="text-center p-4 text-xs font-semibold text-red-500/70 uppercase tracking-wider hidden md:table-cell">H</th>
                    <th className="text-right p-4 text-xs font-semibold text-[#00d4aa]/70 uppercase tracking-wider">Score</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#2d3748]">
                  {leaderboard.map((entry) => {
                    const isMe = entry.userId === data?.currentUserId;
                    const displayName = entry.name || entry.email.split("@")[0];
                    return (
                      <tr
                        key={entry.userId}
                        className={`transition-colors hover:bg-white/5 ${
                          isMe ? "bg-[#00d4aa]/5 border-l-2 border-l-[#00d4aa]" : ""
                        }`}
                      >
                        <td className="p-4">
                          <div className="flex items-center justify-center">
                            <RankBadge rank={entry.rank} />
                          </div>
                        </td>
                        <td className="p-4">
                          <Link href={`/profile/${entry.userId}`} className="flex items-center gap-3 group">
                            <Avatar name={entry.name} image={entry.image} size={8} />
                            <div>
                              <p className={`font-semibold text-sm group-hover:text-[#00d4aa] transition-colors ${isMe ? "text-[#00d4aa]" : "text-white"}`}>
                                {displayName}
                                {isMe && <span className="ml-2 text-[10px] bg-[#00d4aa]/20 text-[#00d4aa] border border-[#00d4aa]/30 px-1.5 py-0.5 rounded-full">You</span>}
                              </p>
                            </div>
                          </Link>
                        </td>
                        <td className="p-4 text-center hidden sm:table-cell">
                          <span className="text-white font-mono text-sm">{entry.totalSolved}</span>
                        </td>
                        <td className="p-4 text-center hidden md:table-cell">
                          <span className="text-green-400 font-mono text-sm">{entry.easyCount}</span>
                        </td>
                        <td className="p-4 text-center hidden md:table-cell">
                          <span className="text-yellow-400 font-mono text-sm">{entry.mediumCount}</span>
                        </td>
                        <td className="p-4 text-center hidden md:table-cell">
                          <span className="text-red-400 font-mono text-sm">{entry.hardCount}</span>
                        </td>
                        <td className="p-4 text-right">
                          <div className="flex items-center justify-end gap-1">
                            <Zap className="w-3.5 h-3.5 text-[#00d4aa]" />
                            <span className="text-[#00d4aa] font-bold font-mono">{entry.score}</span>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <p className="text-center text-gray-600 text-xs mt-4">
              Showing top {leaderboard.length} coders · Score = Easy×1 + Medium×2 + Hard×3
            </p>
          </>
        )}
      </div>
    </div>
  );
}
