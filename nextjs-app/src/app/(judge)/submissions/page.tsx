"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { formatDistanceToNow } from "date-fns";
import { AlertCircle } from "lucide-react";
import { VerdictBadge } from "@/components/ui/VerdictBadge";

export default function SubmissionsPage() {
  const { data: submissions, isLoading, isError, refetch } = useQuery({
    queryKey: ["submissions"],
    queryFn: async () => {
      const res = await fetch("/api/submissions");
      if (!res.ok) throw new Error("Failed to fetch submissions");
      return res.json();
    },
  });

  return (
    <div className="min-h-screen bg-[#0f1419]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-bold text-white mb-8">My Submissions</h1>

        <div className="bg-[#1a1f29] shadow overflow-hidden sm:rounded-lg border border-[#2d3748]">
          <table className="min-w-full divide-y divide-[#2d3748]">
            <thead className="bg-[#2d3748]">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  ID
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Problem
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Language
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Verdict
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Submitted At
                </th>
              </tr>
            </thead>
            <tbody className="bg-[#1a1f29] divide-y divide-[#2d3748]">
              {isLoading ? (
                <tr>
                  <td colSpan={5} className="px-6 py-4 text-center text-gray-500">
                    Loading submissions...
                  </td>
                </tr>
              ) : isError ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center">
                    <AlertCircle className="w-8 h-8 text-red-400 mx-auto mb-2" />
                    <p className="text-red-400 mb-3">Failed to load submissions.</p>
                    <button
                      onClick={() => refetch()}
                      className="text-sm text-[#00d4aa] hover:underline"
                    >
                      Retry
                    </button>
                  </td>
                </tr>
              ) : submissions?.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-4 text-center text-gray-500">
                    You haven't made any submissions yet.{" "}
                    <Link href="/problems" className="text-[#00d4aa] hover:underline">
                      Browse problems →
                    </Link>
                  </td>
                </tr>
              ) : (
                submissions?.map((sub: any) => (
                  <tr key={sub.id} className="hover:bg-white/5 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-mono">
                      #{sub.id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Link
                        href={`/problems/${sub.problem.shortCode}`}
                        className="text-[#00d4aa] hover:text-[#00b38f] font-medium transition-colors"
                      >
                        {sub.problem.name}
                      </Link>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
                      <span className="bg-[#2d3748] px-2 py-1 rounded text-xs font-medium">
                        {sub.language}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <VerdictBadge verdict={sub.verdict} />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDistanceToNow(new Date(sub.submitted), { addSuffix: true })}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
