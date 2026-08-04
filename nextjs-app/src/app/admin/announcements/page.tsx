"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Megaphone, Plus, X, ExternalLink } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import Link from "next/link";

interface Announcement {
  id: number;
  message: string;
  link: string | null;
  isActive: boolean;
  createdAt: string;
}

export default function AdminAnnouncementsPage() {
  const queryClient = useQueryClient();
  const [message, setMessage] = useState("");
  const [link, setLink] = useState("");

  const { data: announcements = [], isLoading } = useQuery<Announcement[]>({
    queryKey: ["adminAnnouncements"],
    queryFn: async () => {
      const res = await fetch("/api/announcements");
      if (!res.ok) return [];
      return res.json();
    },
    staleTime: 10_000,
  });

  const createMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch("/api/announcements", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: message.trim(), link: link.trim() || null }),
      });
      if (!res.ok) throw new Error("Failed to create");
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["adminAnnouncements"] });
      queryClient.invalidateQueries({ queryKey: ["announcements"] });
      setMessage("");
      setLink("");
    },
  });

  const dismissMutation = useMutation({
    mutationFn: async (id: number) => {
      const res = await fetch(`/api/announcements?id=${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error("Failed to dismiss");
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["adminAnnouncements"] });
      queryClient.invalidateQueries({ queryKey: ["announcements"] });
    },
  });

  return (
    <div className="max-w-3xl mx-auto pb-12">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-1">Announcements</h1>
        <p className="text-gray-400 text-sm">Post banners that appear at the top of all pages</p>
      </div>

      {/* Create form */}
      <div className="bg-[#1a1f29] border border-[#2d3748] rounded-xl p-6 mb-6 space-y-4">
        <h2 className="text-white font-semibold flex items-center gap-2">
          <Megaphone className="w-4 h-4 text-[#00d4aa]" />
          New Announcement
        </h2>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Message *</label>
          <input
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="🚀 New feature released! Try the Discussion forum now."
            className="w-full bg-[#0f1419] border border-[#4a5568] rounded-lg p-3 text-white text-sm focus:outline-none focus:border-[#00d4aa] placeholder-gray-600"
          />
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Link (optional)</label>
          <input
            value={link}
            onChange={(e) => setLink(e.target.value)}
            placeholder="/contests or https://..."
            className="w-full bg-[#0f1419] border border-[#4a5568] rounded-lg p-3 text-white text-sm focus:outline-none focus:border-[#00d4aa] placeholder-gray-600"
          />
        </div>

        {/* Preview */}
        {message && (
          <div className="bg-[#00d4aa]/10 border border-[#00d4aa]/30 rounded-lg px-4 py-2.5 flex items-center gap-3 text-sm">
            <Megaphone className="w-4 h-4 text-[#00d4aa] flex-shrink-0" />
            <span className="text-gray-200">{message}</span>
            {link && (
              <span className="ml-auto flex items-center gap-1 text-[#00d4aa] font-semibold text-xs whitespace-nowrap">
                Learn more <ExternalLink className="w-3 h-3" />
              </span>
            )}
          </div>
        )}

        <button
          onClick={() => createMutation.mutate()}
          disabled={!message.trim() || createMutation.isPending}
          className="flex items-center gap-2 px-5 py-2 rounded-lg bg-[#00d4aa] text-[#0f1419] font-semibold text-sm hover:bg-[#00b38f] transition-all disabled:opacity-50"
        >
          <Plus className="w-4 h-4" />
          {createMutation.isPending ? "Posting..." : "Post Announcement"}
        </button>
        {createMutation.isError && (
          <p className="text-red-400 text-sm">{(createMutation.error as Error).message}</p>
        )}
      </div>

      {/* Active announcements */}
      <div>
        <h2 className="text-white font-semibold mb-3 text-sm uppercase tracking-wider text-gray-500">Active Announcements</h2>
        {isLoading ? (
          <div className="space-y-2">
            {[...Array(2)].map((_, i) => (
              <div key={i} className="h-16 bg-[#1a1f29] rounded-xl animate-pulse border border-[#2d3748]" />
            ))}
          </div>
        ) : announcements.length === 0 ? (
          <div className="text-center py-10 text-gray-500">
            <Megaphone className="w-8 h-8 mx-auto mb-2 opacity-40" />
            <p className="text-sm">No active announcements</p>
          </div>
        ) : (
          <div className="space-y-2">
            {announcements.map((ann) => (
              <div key={ann.id} className="bg-[#1a1f29] border border-[#2d3748] rounded-xl px-5 py-4 flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <p className="text-white text-sm font-medium truncate">{ann.message}</p>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="text-gray-500 text-xs">
                      {formatDistanceToNow(new Date(ann.createdAt), { addSuffix: true })}
                    </span>
                    {ann.link && (
                      <Link
                        href={ann.link}
                        target="_blank"
                        className="text-xs text-[#00d4aa] flex items-center gap-1 hover:text-[#00b38f]"
                      >
                        {ann.link} <ExternalLink className="w-3 h-3" />
                      </Link>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => dismissMutation.mutate(ann.id)}
                  disabled={dismissMutation.isPending}
                  className="text-gray-500 hover:text-red-400 transition-colors flex-shrink-0"
                  title="Deactivate"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
