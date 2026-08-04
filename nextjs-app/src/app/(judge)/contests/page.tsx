"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useSession } from "next-auth/react";
import { useState } from "react";
import Link from "next/link";
import {
  Trophy, Clock, Users, Play, CheckCircle, Calendar, Zap, Lock,
} from "lucide-react";
import { formatDistanceToNow, format, isPast, isFuture } from "date-fns";

interface Contest {
  id: number;
  title: string;
  description: string;
  startsAt: string;
  endsAt: string;
  status: "upcoming" | "live" | "past";
  registrationCount: number;
  problemCount: number;
  isPublished: boolean;
}

function StatusBadge({ status }: { status: Contest["status"] }) {
  if (status === "live") {
    return (
      <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-green-400/20 text-green-400 border border-green-400/30">
        <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" />
        LIVE
      </span>
    );
  }
  if (status === "upcoming") {
    return (
      <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-400/20 text-blue-400 border border-blue-400/30">
        <Clock className="w-3 h-3" />
        UPCOMING
      </span>
    );
  }
  return (
    <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-gray-500/20 text-gray-400 border border-gray-500/30">
      ENDED
    </span>
  );
}

function ContestCard({ contest }: { contest: Contest }) {
  const { data: session } = useSession();
  const queryClient = useQueryClient();

  const registerMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`/api/contests/${contest.id}/register`, { method: "POST" });
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contests"] });
    },
  });

  const startsAt = new Date(contest.startsAt);
  const endsAt = new Date(contest.endsAt);

  return (
    <div className={`bg-[#1a1f29] border rounded-xl p-6 hover:border-[#00d4aa]/40 transition-all group ${
      contest.status === "live" ? "border-green-400/30 ring-1 ring-green-400/10" : "border-[#2d3748]"
    }`}>
      <div className="flex items-start justify-between mb-3">
        <StatusBadge status={contest.status} />
        <div className="flex items-center gap-1 text-xs text-gray-500">
          <Users className="w-3.5 h-3.5" />
          {contest.registrationCount} registered
        </div>
      </div>

      <h3 className="text-lg font-bold text-white mb-2 group-hover:text-[#00d4aa] transition-colors">
        {contest.title}
      </h3>
      <p className="text-gray-400 text-sm mb-4 line-clamp-2">{contest.description}</p>

      <div className="flex flex-wrap gap-3 text-xs text-gray-500 mb-4">
        <div className="flex items-center gap-1">
          <Trophy className="w-3.5 h-3.5 text-[#00d4aa]" />
          {contest.problemCount} problems
        </div>
        <div className="flex items-center gap-1">
          <Calendar className="w-3.5 h-3.5" />
          {format(startsAt, "MMM d, yyyy HH:mm")}
        </div>
        <div className="flex items-center gap-1">
          <Clock className="w-3.5 h-3.5" />
          {contest.status === "upcoming"
            ? `Starts ${formatDistanceToNow(startsAt, { addSuffix: true })}`
            : contest.status === "live"
            ? `Ends ${formatDistanceToNow(endsAt, { addSuffix: true })}`
            : `Ended ${formatDistanceToNow(endsAt, { addSuffix: true })}`}
        </div>
      </div>

      <div className="flex gap-2">
        <Link
          href={`/contests/${contest.id}`}
          className="flex-1 text-center px-4 py-2 rounded-lg bg-[#00d4aa]/10 text-[#00d4aa] border border-[#00d4aa]/30 text-sm font-semibold hover:bg-[#00d4aa]/20 transition-all"
        >
          {contest.status === "past" ? "View Results" : "View Contest"}
        </Link>

        {session && contest.status !== "past" && (
          <button
            onClick={() => registerMutation.mutate()}
            disabled={registerMutation.isPending}
            className="px-4 py-2 rounded-lg bg-[#2d3748] text-gray-300 text-sm font-semibold hover:bg-[#00d4aa] hover:text-[#0f1419] transition-all disabled:opacity-50"
          >
            {registerMutation.isPending ? "..." : "Register"}
          </button>
        )}
      </div>
    </div>
  );
}

export default function ContestsPage() {
  const [filter, setFilter] = useState<"all" | "upcoming" | "live" | "past">("all");

  const { data: contests = [], isLoading } = useQuery<Contest[]>({
    queryKey: ["contests", filter],
    queryFn: async () => {
      const res = await fetch(`/api/contests?filter=${filter}`);
      if (!res.ok) return [];
      return res.json();
    },
    staleTime: 30_000,
  });

  const filters: { value: typeof filter; label: string }[] = [
    { value: "all", label: "All" },
    { value: "live", label: "🔴 Live" },
    { value: "upcoming", label: "⏳ Upcoming" },
    { value: "past", label: "📜 Past" },
  ];

  return (
    <div className="min-h-screen bg-[#0f1419]">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {/* Header */}
        <div className="mb-8 text-center">
          <div className="inline-flex items-center gap-3 mb-3">
            <Zap className="w-8 h-8 text-[#00d4aa]" />
            <h1 className="text-4xl font-bold text-white">Contests</h1>
          </div>
          <p className="text-gray-400">Compete in timed coding challenges and climb the rankings</p>
        </div>

        {/* Filter tabs */}
        <div className="flex gap-2 mb-8 justify-center flex-wrap">
          {filters.map((f) => (
            <button
              key={f.value}
              onClick={() => setFilter(f.value)}
              className={`px-5 py-2 rounded-full text-sm font-semibold transition-all border ${
                filter === f.value
                  ? "bg-[#00d4aa] text-[#0f1419] border-[#00d4aa]"
                  : "bg-transparent text-gray-400 border-[#2d3748] hover:border-gray-500 hover:text-gray-200"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        {isLoading ? (
          <div className="grid gap-4 md:grid-cols-2">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-48 bg-[#1a1f29] rounded-xl animate-pulse border border-[#2d3748]" />
            ))}
          </div>
        ) : contests.length === 0 ? (
          <div className="text-center py-20">
            <Trophy className="w-12 h-12 text-gray-600 mx-auto mb-3" />
            <p className="text-gray-400">No contests found for this filter.</p>
            <p className="text-gray-600 text-sm mt-1">Check back soon for upcoming contests!</p>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {contests.map((c) => (
              <ContestCard key={c.id} contest={c} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
