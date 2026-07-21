"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { History, ChevronLeft, ChevronRight } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { VerdictBadge } from "@/components/ui/VerdictBadge";

const PAGE_LIMIT = 20;

export default function AdminSubmissionsList() {
  const [page, setPage] = useState(1);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["adminAllSubmissions", page],
    queryFn: async () => {
      const res = await fetch(`/api/admin/submissions?page=${page}&limit=${PAGE_LIMIT}`);
      if (!res.ok) throw new Error("Failed to fetch submissions");
      return res.json();
    },
  });

  const submissions = data?.submissions ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.ceil(total / PAGE_LIMIT);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center bg-[#1a1f29] p-6 rounded-[15px] border border-[#2d3748]">
        <h1 className="text-2xl font-bold text-white flex items-center gap-3">
          <History className="text-[#00d4aa]" /> All Submissions
        </h1>
        <span className="text-gray-400 text-sm">{total} total</span>
      </div>

      <div className="bg-[#1a1f29] rounded-[15px] border border-[#2d3748] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-[#2d3748] text-[#a0aec0] text-sm uppercase tracking-wider">
                <th className="p-4 font-semibold">ID</th>
                <th className="p-4 font-semibold">User</th>
                <th className="p-4 font-semibold">Problem</th>
                <th className="p-4 font-semibold">Language</th>
                <th className="p-4 font-semibold">Verdict</th>
                <th className="p-4 font-semibold">Submitted At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#2d3748]">
              {isLoading ? (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-gray-400">
                    Loading submissions...
                  </td>
                </tr>
              ) : isError ? (
                <tr>
                  <td colSpan={6} className="p-8 text-center">
                    <p className="text-red-400 mb-3">Failed to load submissions.</p>
                    <button
                      onClick={() => refetch()}
                      className="text-sm text-[#00d4aa] hover:underline"
                    >
                      Retry
                    </button>
                  </td>
                </tr>
              ) : submissions.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-gray-400">
                    No submissions found.
                  </td>
                </tr>
              ) : (
                submissions.map((sub: any) => (
                  <tr key={sub.id} className="hover:bg-white/5 transition-colors">
                    <td className="p-4 text-gray-400 font-mono">#{sub.id}</td>
                    <td className="p-4 text-white">
                      {sub.user?.name || sub.user?.email || "Unknown"}
                    </td>
                    <td className="p-4 text-[#00d4aa] font-medium">
                      {sub.problem?.name || "Unknown"}
                    </td>
                    <td className="p-4 text-gray-300 text-sm">
                      <span className="bg-[#2d3748] px-2 py-1 rounded">
                        {sub.language}
                      </span>
                    </td>
                    <td className="p-4">
                      <VerdictBadge verdict={sub.verdict} />
                    </td>
                    <td className="p-4 text-gray-400 text-sm">
                      {formatDistanceToNow(new Date(sub.submitted), { addSuffix: true })}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-[#2d3748]">
            <p className="text-sm text-gray-400">
              Page {page} of {totalPages}
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="p-2 rounded text-gray-300 hover:text-white hover:bg-[#2d3748] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="p-2 rounded text-gray-300 hover:text-white hover:bg-[#2d3748] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
