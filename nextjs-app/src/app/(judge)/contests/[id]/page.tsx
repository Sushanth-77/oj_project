"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useSession } from "next-auth/react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  Trophy, Clock, Users, ArrowLeft, Crown, Medal, Zap,
  CheckCircle, Circle, ExternalLink, Lock,
} from "lucide-react";
import { formatDistanceToNow, format, differenceInSeconds } from "date-fns";
import { useState, useEffect } from "react";

const DIFF_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  E: { label: "Easy",   color: "text-green-400",  bg: "bg-green-400/20 border-green-400/30" },
  M: { label: "Medium", color: "text-yellow-400", bg: "bg-yellow-400/20 border-yellow-400/30" },
  H: { label: "Hard",   color: "text-red-400",    bg: "bg-red-400/20 border-red-400/30" },
};

function Countdown({ endsAt }: { endsAt: string }) {
  const [seconds, setSeconds] = useState(() =>
    Math.max(0, differenceInSeconds(new Date(endsAt), new Date()))
  );

  useEffect(() => {
    const interval = setInterval(() => {
      setSeconds((s) => Math.max(0, s - 1));
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;

  return (
    <div className="flex items-center gap-1 font-mono text-2xl font-bold text-[#00d4aa]">
      <span>{String(h).padStart(2, "0")}</span>
      <span className="animate-pulse">:</span>
      <span>{String(m).padStart(2, "0")}</span>
      <span className="animate-pulse">:</span>
      <span>{String(s).padStart(2, "0")}</span>
    </div>
  );
}

function RankBadge({ rank }: { rank: number }) {
  if (rank === 1) return <Crown className="w-5 h-5 text-yellow-400" />;
  if (rank === 2) return <Medal className="w-5 h-5 text-gray-300" />;
  if (rank === 3) return <Medal className="w-5 h-5 text-amber-600" />;
  return <span className="text-gray-500 font-mono text-sm w-5 text-center">{rank}</span>;
}

export default function ContestDetailPage() {
  const params = useParams();
  const contestId = params.id as string;
  const { data: session } = useSession();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<"problems" | "scoreboard">("problems");

  const { data: contest, isLoading } = useQuery({
    queryKey: ["contest", contestId],
    queryFn: async () => {
      const res = await fetch(`/api/contests/${contestId}`);
      if (!res.ok) throw new Error("Failed to load");
      return res.json();
    },
    refetchInterval: 30_000,
  });

  const registerMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`/api/contests/${contestId}/register`, { method: "POST" });
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contest", contestId] });
    },
  });

  if (isLoading) {
    return <div className="p-8 text-center text-gray-400">Loading contest...</div>;
  }
  if (!contest) {
    return <div className="p-8 text-center text-red-400">Contest not found.</div>;
  }

  const isLive = contest.status === "live";
  const isUpcoming = contest.status === "upcoming";

  return (
    <div className="min-h-screen bg-[#0f1419]">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Back */}
        <Link href="/contests" className="inline-flex items-center gap-2 text-[#00d4aa] text-sm mb-6 hover:text-[#00b38f]">
          <ArrowLeft className="w-4 h-4" />
          Back to Contests
        </Link>

        {/* Header */}
        <div className="bg-[#1a1f29] rounded-2xl border border-[#2d3748] p-6 mb-6">
          <div className="flex flex-wrap items-start justify-between gap-4 mb-4">
            <div>
              <div className="flex items-center gap-3 mb-2">
                {isLive && (
                  <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-green-400/20 text-green-400 border border-green-400/30">
                    <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" />
                    LIVE
                  </span>
                )}
                {isUpcoming && (
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-400/20 text-blue-400 border border-blue-400/30">
                    UPCOMING
                  </span>
                )}
              </div>
              <h1 className="text-3xl font-bold text-white mb-2">{contest.title}</h1>
              <p className="text-gray-400">{contest.description}</p>
            </div>

            {session && !isLive && !isUpcoming ? null : session ? (
              <button
                onClick={() => registerMutation.mutate()}
                disabled={registerMutation.isPending}
                className={`px-6 py-2.5 rounded-lg font-semibold text-sm transition-all ${
                  contest.isRegistered
                    ? "bg-red-500/10 border border-red-500/30 text-red-400 hover:bg-red-500/20"
                    : "bg-[#00d4aa] text-[#0f1419] hover:bg-[#00b38f]"
                } disabled:opacity-50`}
              >
                {registerMutation.isPending ? "..." : contest.isRegistered ? "Unregister" : "Register Now"}
              </button>
            ) : null}
          </div>

          {/* Stats */}
          <div className="flex flex-wrap gap-6 text-sm text-gray-400 mt-4 pt-4 border-t border-[#2d3748]">
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4 text-[#00d4aa]" />
              <span>{contest.registrationCount} participants</span>
            </div>
            <div className="flex items-center gap-2">
              <Trophy className="w-4 h-4 text-yellow-400" />
              <span>{contest.problems?.length} problems</span>
            </div>
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4" />
              <span>
                {format(new Date(contest.startsAt), "MMM d, HH:mm")} – {format(new Date(contest.endsAt), "MMM d, HH:mm")}
              </span>
            </div>
          </div>

          {/* Live countdown */}
          {isLive && (
            <div className="mt-4 pt-4 border-t border-[#2d3748] flex items-center gap-3">
              <span className="text-gray-500 text-sm">Time remaining:</span>
              <Countdown endsAt={contest.endsAt} />
            </div>
          )}

          {/* Upcoming countdown */}
          {isUpcoming && (
            <div className="mt-4 pt-4 border-t border-[#2d3748]">
              <p className="text-blue-400 text-sm">
                🕐 Starts {formatDistanceToNow(new Date(contest.startsAt), { addSuffix: true })}
              </p>
            </div>
          )}
        </div>

        {/* Tabs */}
        <div className="flex gap-0 border-b border-[#2d3748] mb-6">
          {(["problems", "scoreboard"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-6 py-3 text-sm font-semibold border-b-2 transition-colors capitalize ${
                tab === t
                  ? "border-[#00d4aa] text-[#00d4aa]"
                  : "border-transparent text-gray-500 hover:text-gray-300"
              }`}
            >
              {t}
            </button>
          ))}
        </div>

        {/* Problems tab */}
        {tab === "problems" && (
          <div className="space-y-3">
            {isUpcoming && !contest.isRegistered && (
              <div className="bg-blue-400/10 border border-blue-400/20 rounded-xl p-4 text-blue-300 text-sm text-center">
                Register to participate in this contest
              </div>
            )}
            {contest.problems?.map((cp: any, idx: number) => {
              const d = DIFF_CONFIG[cp.problem.difficulty];
              const canView = !isUpcoming || (isUpcoming && false); // hide problems until live
              return (
                <div
                  key={cp.id}
                  className={`bg-[#1a1f29] border border-[#2d3748] rounded-xl p-4 flex items-center justify-between ${
                    isUpcoming ? "opacity-60" : "hover:border-[#00d4aa]/30"
                  } transition-all`}
                >
                  <div className="flex items-center gap-4">
                    <span className="text-gray-500 font-mono text-sm w-6">{idx + 1}</span>
                    <div>
                      {isUpcoming ? (
                        <p className="text-gray-400 font-semibold flex items-center gap-2">
                          <Lock className="w-4 h-4" />
                          {cp.problem.name}
                        </p>
                      ) : (
                        <Link
                          href={`/problems/${cp.problem.shortCode}`}
                          className="text-white font-semibold hover:text-[#00d4aa] transition-colors"
                        >
                          {cp.problem.name}
                        </Link>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${d.bg} ${d.color}`}>
                      {d.label}
                    </span>
                    <span className="text-[#00d4aa] font-mono text-sm font-bold">{cp.points} pts</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Scoreboard tab */}
        {tab === "scoreboard" && (
          <div className="bg-[#1a1f29] rounded-xl border border-[#2d3748] overflow-hidden">
            {contest.scoreboard?.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                <Trophy className="w-10 h-10 mx-auto mb-2 opacity-30" />
                {isUpcoming ? "Scoreboard available after contest starts" : "No submissions yet"}
              </div>
            ) : (
              <table className="w-full">
                <thead>
                  <tr className="border-b border-[#2d3748]">
                    <th className="text-left p-4 text-xs font-semibold text-gray-500 uppercase w-12">Rank</th>
                    <th className="text-left p-4 text-xs font-semibold text-gray-500 uppercase">User</th>
                    <th className="text-center p-4 text-xs font-semibold text-gray-500 uppercase">Solved</th>
                    <th className="text-right p-4 text-xs font-semibold text-[#00d4aa]/70 uppercase">Score</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#2d3748]">
                  {contest.scoreboard?.map((entry: any) => {
                    const isMe = entry.userId === session?.user?.id;
                    return (
                      <tr key={entry.userId} className={`hover:bg-white/5 transition-colors ${isMe ? "bg-[#00d4aa]/5 border-l-2 border-l-[#00d4aa]" : ""}`}>
                        <td className="p-4">
                          <div className="flex items-center justify-center">
                            <RankBadge rank={entry.rank} />
                          </div>
                        </td>
                        <td className="p-4">
                          <Link href={`/profile/${entry.userId}`} className="flex items-center gap-3 group">
                            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#00d4aa] to-[#00b894] flex items-center justify-center text-white font-bold text-xs">
                              {(entry.name || entry.email || "?")[0].toUpperCase()}
                            </div>
                            <span className={`font-semibold text-sm group-hover:text-[#00d4aa] transition-colors ${isMe ? "text-[#00d4aa]" : "text-white"}`}>
                              {entry.name || entry.email?.split("@")[0]}
                              {isMe && <span className="ml-2 text-[10px] bg-[#00d4aa]/20 text-[#00d4aa] border border-[#00d4aa]/30 px-1.5 py-0.5 rounded-full">You</span>}
                            </span>
                          </Link>
                        </td>
                        <td className="p-4 text-center text-white font-mono">{entry.solved}</td>
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
            )}
          </div>
        )}
      </div>
    </div>
  );
}
