"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { format } from "date-fns";
import { Plus, Trash2, Trophy, CheckCircle, Clock } from "lucide-react";

interface Contest {
  id: number;
  title: string;
  description: string;
  startsAt: string;
  endsAt: string;
  isPublished: boolean;
  status: "upcoming" | "live" | "past";
  registrationCount: number;
  problemCount: number;
}

export default function AdminContestsPage() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    title: "",
    description: "",
    startsAt: "",
    endsAt: "",
    isPublished: false,
  });

  const { data: contests = [], isLoading } = useQuery<Contest[]>({
    queryKey: ["adminContests"],
    queryFn: async () => {
      const res = await fetch("/api/contests?filter=all");
      if (!res.ok) return [];
      return res.json();
    },
  });

  const createMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch("/api/contests", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (!res.ok) throw new Error("Failed to create contest");
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["adminContests"] });
      setShowForm(false);
      setForm({ title: "", description: "", startsAt: "", endsAt: "", isPublished: false });
    },
  });

  return (
    <div className="max-w-5xl mx-auto pb-12">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white mb-1">Contests</h1>
          <p className="text-gray-400 text-sm">Create and manage coding contests</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[#00d4aa] text-[#0f1419] font-semibold text-sm hover:bg-[#00b38f] transition-all"
        >
          <Plus className="w-4 h-4" />
          New Contest
        </button>
      </div>

      {/* Create Form */}
      {showForm && (
        <div className="bg-[#1a1f29] border border-[#2d3748] rounded-xl p-6 mb-6 space-y-4">
          <h2 className="text-white font-semibold text-lg">Create Contest</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-gray-400 text-sm mb-1">Title *</label>
              <input
                value={form.title}
                onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
                className="w-full bg-[#0f1419] border border-[#4a5568] rounded-lg p-3 text-white text-sm focus:outline-none focus:border-[#00d4aa]"
                placeholder="Weekly Contest #1"
              />
            </div>
            <div>
              <label className="block text-gray-400 text-sm mb-1">Description</label>
              <input
                value={form.description}
                onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                className="w-full bg-[#0f1419] border border-[#4a5568] rounded-lg p-3 text-white text-sm focus:outline-none focus:border-[#00d4aa]"
                placeholder="Compete and win!"
              />
            </div>
            <div>
              <label className="block text-gray-400 text-sm mb-1">Starts At *</label>
              <input
                type="datetime-local"
                value={form.startsAt}
                onChange={(e) => setForm((f) => ({ ...f, startsAt: e.target.value }))}
                className="w-full bg-[#0f1419] border border-[#4a5568] rounded-lg p-3 text-white text-sm focus:outline-none focus:border-[#00d4aa]"
              />
            </div>
            <div>
              <label className="block text-gray-400 text-sm mb-1">Ends At *</label>
              <input
                type="datetime-local"
                value={form.endsAt}
                onChange={(e) => setForm((f) => ({ ...f, endsAt: e.target.value }))}
                className="w-full bg-[#0f1419] border border-[#4a5568] rounded-lg p-3 text-white text-sm focus:outline-none focus:border-[#00d4aa]"
              />
            </div>
          </div>
          <label className="flex items-center gap-3 cursor-pointer">
            <div
              onClick={() => setForm((f) => ({ ...f, isPublished: !f.isPublished }))}
              className={`w-10 h-5 rounded-full transition-colors relative ${form.isPublished ? "bg-[#00d4aa]" : "bg-[#2d3748]"}`}
            >
              <span className={`absolute top-0.5 w-4 h-4 rounded-full bg-white transition-all ${form.isPublished ? "left-5" : "left-0.5"}`} />
            </div>
            <span className="text-gray-300 text-sm">Published (visible to users)</span>
          </label>
          <div className="flex gap-3">
            <button
              onClick={() => createMutation.mutate()}
              disabled={!form.title || !form.startsAt || !form.endsAt || createMutation.isPending}
              className="px-5 py-2 rounded-lg bg-[#00d4aa] text-[#0f1419] font-semibold text-sm hover:bg-[#00b38f] transition-all disabled:opacity-50"
            >
              {createMutation.isPending ? "Creating..." : "Create Contest"}
            </button>
            <button
              onClick={() => setShowForm(false)}
              className="px-5 py-2 rounded-lg bg-[#2d3748] text-gray-300 text-sm hover:bg-[#3d4758] transition-all"
            >
              Cancel
            </button>
          </div>
          {createMutation.isError && (
            <p className="text-red-400 text-sm">{(createMutation.error as Error).message}</p>
          )}
        </div>
      )}

      {/* Contests list */}
      {isLoading ? (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-20 bg-[#1a1f29] rounded-xl animate-pulse border border-[#2d3748]" />
          ))}
        </div>
      ) : contests.length === 0 ? (
        <div className="text-center py-20">
          <Trophy className="w-12 h-12 text-gray-600 mx-auto mb-3" />
          <p className="text-gray-400">No contests yet. Create your first one!</p>
        </div>
      ) : (
        <div className="bg-[#1a1f29] rounded-xl border border-[#2d3748] overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-[#2d3748]">
                <th className="text-left p-4 text-xs font-semibold text-gray-500 uppercase">Title</th>
                <th className="text-left p-4 text-xs font-semibold text-gray-500 uppercase hidden sm:table-cell">Status</th>
                <th className="text-left p-4 text-xs font-semibold text-gray-500 uppercase hidden md:table-cell">Start</th>
                <th className="text-left p-4 text-xs font-semibold text-gray-500 uppercase hidden md:table-cell">End</th>
                <th className="text-center p-4 text-xs font-semibold text-gray-500 uppercase">Published</th>
                <th className="text-center p-4 text-xs font-semibold text-gray-500 uppercase">Registered</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#2d3748]">
              {contests.map((c) => (
                <tr key={c.id} className="hover:bg-white/5 transition-colors">
                  <td className="p-4">
                    <span className="text-white font-semibold text-sm">{c.title}</span>
                    {c.description && (
                      <p className="text-gray-500 text-xs mt-0.5 truncate max-w-xs">{c.description}</p>
                    )}
                  </td>
                  <td className="p-4 hidden sm:table-cell">
                    {c.status === "live" ? (
                      <span className="flex items-center gap-1.5 text-xs font-bold text-green-400">
                        <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" /> LIVE
                      </span>
                    ) : c.status === "upcoming" ? (
                      <span className="flex items-center gap-1 text-xs font-bold text-blue-400">
                        <Clock className="w-3 h-3" /> UPCOMING
                      </span>
                    ) : (
                      <span className="text-xs text-gray-500 font-bold">ENDED</span>
                    )}
                  </td>
                  <td className="p-4 text-gray-400 text-xs hidden md:table-cell">
                    {format(new Date(c.startsAt), "MMM d, HH:mm")}
                  </td>
                  <td className="p-4 text-gray-400 text-xs hidden md:table-cell">
                    {format(new Date(c.endsAt), "MMM d, HH:mm")}
                  </td>
                  <td className="p-4 text-center">
                    {c.isPublished ? (
                      <CheckCircle className="w-4 h-4 text-green-400 inline" />
                    ) : (
                      <span className="text-gray-600 text-xs">Draft</span>
                    )}
                  </td>
                  <td className="p-4 text-center text-white font-mono text-sm">{c.registrationCount}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
