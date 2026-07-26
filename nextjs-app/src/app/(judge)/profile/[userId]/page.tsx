"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import Link from "next/link";
import { formatDistanceToNow, format, parseISO } from "date-fns";
import {
  Calendar, Flame, Zap, Trophy, Star, ArrowLeft, ExternalLink,
} from "lucide-react";
import { ProfileData } from "@/types";
import { VerdictBadge } from "@/components/ui/VerdictBadge";

// ─── Submission Heatmap ───────────────────────────────────────────────────────
function SubmissionHeatmap({ heatmap }: { heatmap: Record<string, number> }) {
  // Build last 52 weeks of days
  const today = new Date();
  const startDate = new Date(today);
  startDate.setDate(today.getDate() - 364);

  const weeks: { date: string; count: number }[][] = [];
  let currentWeek: { date: string; count: number }[] = [];

  for (let d = new Date(startDate); d <= today; d.setDate(d.getDate() + 1)) {
    const dateStr = d.toISOString().split("T")[0];
    const count = heatmap[dateStr] ?? 0;
    currentWeek.push({ date: dateStr, count });
    if (currentWeek.length === 7) {
      weeks.push(currentWeek);
      currentWeek = [];
    }
  }
  if (currentWeek.length > 0) weeks.push(currentWeek);

  const maxCount = Math.max(...Object.values(heatmap), 1);

  const getColor = (count: number) => {
    if (count === 0) return "bg-[#2d3748]";
    const intensity = count / maxCount;
    if (intensity < 0.25) return "bg-[#00d4aa]/30";
    if (intensity < 0.5)  return "bg-[#00d4aa]/55";
    if (intensity < 0.75) return "bg-[#00d4aa]/80";
    return "bg-[#00d4aa]";
  };

  const months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  const totalActivity = Object.values(heatmap).reduce((a, b) => a + b, 0);

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-gray-500" />
          <span className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Activity</span>
        </div>
        <span className="text-xs text-gray-500">{totalActivity} submissions in the last year</span>
      </div>
      <div className="overflow-x-auto pb-2">
        <div className="flex gap-1 min-w-max">
          {weeks.map((week, wi) => (
            <div key={wi} className="flex flex-col gap-1">
              {week.map((day) => (
                <div
                  key={day.date}
                  title={`${day.date}: ${day.count} submission${day.count !== 1 ? "s" : ""}`}
                  className={`w-3 h-3 rounded-sm transition-all ${getColor(day.count)}`}
                />
              ))}
            </div>
          ))}
        </div>
      </div>
      <div className="flex justify-end items-center gap-1 mt-2">
        <span className="text-xs text-gray-600">Less</span>
        {["bg-[#2d3748]","bg-[#00d4aa]/30","bg-[#00d4aa]/55","bg-[#00d4aa]/80","bg-[#00d4aa]"].map((c,i) => (
          <div key={i} className={`w-3 h-3 rounded-sm ${c}`} />
        ))}
        <span className="text-xs text-gray-600">More</span>
      </div>
    </div>
  );
}

// ─── Badge Card ──────────────────────────────────────────────────────────────
function BadgeCard({ icon, name, description }: { icon: string; name: string; description: string }) {
  return (
    <div className="group flex flex-col items-center gap-1.5 p-3 bg-[#0f1419] rounded-xl border border-[#2d3748] hover:border-[#00d4aa]/40 transition-all" title={description}>
      <span className="text-2xl">{icon}</span>
      <span className="text-xs font-semibold text-gray-300 text-center leading-tight">{name}</span>
    </div>
  );
}

// ─── Donut Chart ─────────────────────────────────────────────────────────────
function SolveDonut({ easy, medium, hard, total }: { easy: number; medium: number; hard: number; total: number }) {
  const size = 120;
  const strokeW = 14;
  const r = (size - strokeW) / 2;
  const circ = 2 * Math.PI * r;

  const easyPct   = total > 0 ? easy / total : 0;
  const mediumPct = total > 0 ? medium / total : 0;
  const hardPct   = total > 0 ? hard / total : 0;

  const easyLen   = easyPct * circ;
  const mediumLen = mediumPct * circ;
  const hardLen   = hardPct * circ;

  const easyOffset   = 0;
  const mediumOffset = -easyLen;
  const hardOffset   = -(easyLen + mediumLen);

  return (
    <div className="flex flex-col items-center">
      <div className="relative">
        <svg width={size} height={size} className="-rotate-90">
          {/* BG ring */}
          <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="#2d3748" strokeWidth={strokeW} />
          {/* Easy */}
          {easyLen > 0 && (
            <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="#4ade80" strokeWidth={strokeW}
              strokeDasharray={`${easyLen} ${circ - easyLen}`} strokeDashoffset={easyOffset} strokeLinecap="round" />
          )}
          {/* Medium */}
          {mediumLen > 0 && (
            <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="#facc15" strokeWidth={strokeW}
              strokeDasharray={`${mediumLen} ${circ - mediumLen}`} strokeDashoffset={mediumOffset} strokeLinecap="round" />
          )}
          {/* Hard */}
          {hardLen > 0 && (
            <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="#f87171" strokeWidth={strokeW}
              strokeDasharray={`${hardLen} ${circ - hardLen}`} strokeDashoffset={hardOffset} strokeLinecap="round" />
          )}
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold text-white">{total}</span>
          <span className="text-xs text-gray-500">Solved</span>
        </div>
      </div>
      <div className="flex gap-4 mt-3 text-xs">
        <span className="text-green-400"><span className="font-bold">{easy}</span> Easy</span>
        <span className="text-yellow-400"><span className="font-bold">{medium}</span> Med</span>
        <span className="text-red-400"><span className="font-bold">{hard}</span> Hard</span>
      </div>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function ProfilePage() {
  const params = useParams();
  const userId = params.userId as string;

  const { data, isLoading, isError } = useQuery<ProfileData>({
    queryKey: ["profile", userId],
    queryFn: async () => {
      const res = await fetch(`/api/profile/${userId}`);
      if (!res.ok) throw new Error("Failed to fetch profile");
      return res.json();
    },
    staleTime: 60_000,
  });

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
        <p className="text-red-400 text-lg">User not found.</p>
        <Link href="/problems" className="text-[#00d4aa] hover:underline">← Back to Problems</Link>
      </div>
    );
  }

  const { user, stats, badges, heatmap, recentSubmissions } = data;
  const displayName = user.name || user.email?.split("@")[0] || "Anonymous";
  const joinDate = format(new Date(user.createdAt), "MMM yyyy");

  return (
    <div className="min-h-screen bg-[#0f1419]">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">

        <Link href="/leaderboard" className="inline-flex items-center gap-1 text-sm text-[#00d4aa] hover:text-[#00b38f] mb-6 transition-colors">
          <ArrowLeft className="w-4 h-4" />
          Back to Leaderboard
        </Link>

        {/* Profile Header */}
        <div className="bg-[#1a1f29] rounded-2xl border border-[#2d3748] p-6 mb-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-5">
            {/* Avatar */}
            {user.image ? (
              <img src={user.image} alt={displayName} className="w-20 h-20 rounded-full ring-4 ring-[#00d4aa]/30" />
            ) : (
              <div className="w-20 h-20 rounded-full bg-gradient-to-br from-[#00d4aa] to-[#00b894] flex items-center justify-center text-white font-bold text-3xl ring-4 ring-[#00d4aa]/30">
                {displayName[0]?.toUpperCase()}
              </div>
            )}

            <div className="flex-1">
              <h1 className="text-2xl font-bold text-white">{displayName}</h1>
              {user.email && <p className="text-gray-400 text-sm mt-0.5">{user.email}</p>}
              <p className="text-gray-600 text-xs mt-1">Member since {joinDate}</p>

              {/* Streak pills */}
              <div className="flex flex-wrap gap-3 mt-3">
                <div className="flex items-center gap-1.5 bg-orange-500/10 border border-orange-500/30 rounded-full px-3 py-1">
                  <Flame className="w-4 h-4 text-orange-400" />
                  <span className="text-orange-400 text-sm font-semibold">{stats.currentStreak}d streak</span>
                </div>
                <div className="flex items-center gap-1.5 bg-[#00d4aa]/10 border border-[#00d4aa]/30 rounded-full px-3 py-1">
                  <Zap className="w-4 h-4 text-[#00d4aa]" />
                  <span className="text-[#00d4aa] text-sm font-semibold">{stats.score} pts</span>
                </div>
                {stats.longestStreak > 0 && (
                  <div className="flex items-center gap-1.5 bg-purple-500/10 border border-purple-500/30 rounded-full px-3 py-1">
                    <Star className="w-4 h-4 text-purple-400" />
                    <span className="text-purple-400 text-sm font-semibold">Best: {stats.longestStreak}d</span>
                  </div>
                )}
              </div>
            </div>

            {/* Score box */}
            <div className="text-right">
              <div className="text-3xl font-bold text-[#00d4aa]">#{stats.score}</div>
              <div className="text-xs text-gray-500">score</div>
            </div>
          </div>
        </div>

        {/* Stats + Donut */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          {/* Donut */}
          <div className="bg-[#1a1f29] rounded-xl border border-[#2d3748] p-5 flex flex-col items-center justify-center">
            <SolveDonut
              easy={stats.easyCount}
              medium={stats.mediumCount}
              hard={stats.hardCount}
              total={stats.totalSolved}
            />
            <div className="mt-3 text-center">
              <p className="text-xs text-gray-500">
                {stats.totalSolved} / {stats.totalProblems} problems solved
              </p>
              <div className="w-full bg-[#2d3748] rounded-full h-1.5 mt-2">
                <div
                  className="h-1.5 rounded-full bg-[#00d4aa] transition-all duration-500"
                  style={{ width: `${stats.totalProblems > 0 ? (stats.totalSolved / stats.totalProblems) * 100 : 0}%` }}
                />
              </div>
            </div>
          </div>

          {/* Stat Cards */}
          <div className="md:col-span-2 grid grid-cols-2 gap-4">
            {[
              { label: "Easy Solved",   value: stats.easyCount,   color: "text-green-400",  bg: "from-green-400/10" },
              { label: "Medium Solved", value: stats.mediumCount, color: "text-yellow-400", bg: "from-yellow-400/10" },
              { label: "Hard Solved",   value: stats.hardCount,   color: "text-red-400",    bg: "from-red-400/10" },
              { label: "Total Score",   value: stats.score,       color: "text-[#00d4aa]",  bg: "from-[#00d4aa]/10" },
            ].map((stat) => (
              <div key={stat.label} className={`bg-gradient-to-br ${stat.bg} to-transparent bg-[#1a1f29] rounded-xl border border-[#2d3748] p-4`}>
                <p className="text-gray-500 text-xs font-medium uppercase tracking-wider mb-1">{stat.label}</p>
                <p className={`text-3xl font-bold ${stat.color}`}>{stat.value}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Activity Heatmap */}
        <div className="bg-[#1a1f29] rounded-xl border border-[#2d3748] p-5 mb-6">
          <SubmissionHeatmap heatmap={heatmap} />
        </div>

        {/* Badges */}
        {badges.length > 0 && (
          <div className="bg-[#1a1f29] rounded-xl border border-[#2d3748] p-5 mb-6">
            <div className="flex items-center gap-2 mb-4">
              <Trophy className="w-4 h-4 text-yellow-400" />
              <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Achievements</h2>
              <span className="ml-auto text-xs text-gray-600">{badges.length} earned</span>
            </div>
            <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-3">
              {badges.map((badge) => (
                <BadgeCard key={badge.slug} icon={badge.icon} name={badge.name} description={badge.description} />
              ))}
            </div>
          </div>
        )}

        {/* Recent Submissions */}
        {recentSubmissions.length > 0 && (
          <div className="bg-[#1a1f29] rounded-xl border border-[#2d3748] overflow-hidden">
            <div className="flex items-center justify-between px-5 py-4 border-b border-[#2d3748]">
              <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Recent Activity</h2>
            </div>
            <table className="w-full">
              <tbody className="divide-y divide-[#2d3748]">
                {recentSubmissions.map((sub) => (
                  <tr key={sub.id} className="hover:bg-white/5 transition-colors group">
                    <td className="px-5 py-3">
                      <Link
                        href={`/problems/${sub.problem.shortCode}`}
                        className="text-sm font-medium text-white group-hover:text-[#00d4aa] transition-colors flex items-center gap-1"
                      >
                        {sub.problem.name}
                        <ExternalLink className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </Link>
                      <p className="text-xs text-gray-500 mt-0.5">
                        {formatDistanceToNow(new Date(sub.submitted), { addSuffix: true })} · {sub.language}
                      </p>
                    </td>
                    <td className="px-5 py-3 text-right">
                      <VerdictBadge verdict={sub.verdict} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
