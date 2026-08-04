"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Megaphone, X, ExternalLink } from "lucide-react";
import Link from "next/link";

interface Announcement {
  id: number;
  message: string;
  link: string | null;
  createdAt: string;
}

export function AnnouncementBanner() {
  const [dismissed, setDismissed] = useState<Set<number>>(new Set());

  const { data: announcements = [] } = useQuery<Announcement[]>({
    queryKey: ["announcements"],
    queryFn: async () => {
      const res = await fetch("/api/announcements");
      if (!res.ok) return [];
      return res.json();
    },
    staleTime: 5 * 60_000,
    refetchInterval: 5 * 60_000,
  });

  const visible = announcements.filter((a) => !dismissed.has(a.id));

  if (visible.length === 0) return null;

  return (
    <div className="flex flex-col gap-0">
      {visible.map((ann) => (
        <div
          key={ann.id}
          className="relative flex items-center justify-center gap-3 bg-gradient-to-r from-[#00d4aa]/20 via-[#00d4aa]/10 to-[#00d4aa]/20 border-b border-[#00d4aa]/30 px-6 py-2.5 text-sm"
        >
          <Megaphone className="w-4 h-4 text-[#00d4aa] flex-shrink-0" />
          <span className="text-gray-200 text-center">
            {ann.message}
            {ann.link && (
              <Link
                href={ann.link}
                className="ml-2 inline-flex items-center gap-1 text-[#00d4aa] font-semibold hover:text-[#00b38f] transition-colors"
              >
                Learn more <ExternalLink className="w-3 h-3" />
              </Link>
            )}
          </span>
          <button
            onClick={() => setDismissed((prev) => new Set([...prev, ann.id]))}
            className="absolute right-3 text-gray-500 hover:text-gray-200 transition-colors"
            title="Dismiss"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      ))}
    </div>
  );
}
