"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { PlusCircle, Edit, Trash2, List } from "lucide-react";
import { format } from "date-fns";
import { Problem } from "@/types";

export default function AdminProblemsList() {
  const queryClient = useQueryClient();

  const { data: problems, isLoading } = useQuery<Problem[]>({
    queryKey: ["adminProblems"],
    queryFn: async () => {
      const res = await fetch("/api/admin/problems");
      if (!res.ok) throw new Error("Failed to fetch problems");
      return res.json();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      const res = await fetch(`/api/admin/problems?id=${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error("Failed to delete problem");
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["adminProblems"] });
    },
  });

  const handleDelete = (id: number) => {
    if (confirm("Are you sure you want to delete this problem?")) {
      deleteMutation.mutate(id);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center bg-[#1a1f29] p-6 rounded-[15px] border border-[#2d3748]">
        <h1 className="text-2xl font-bold text-white flex items-center gap-3">
          <List className="text-[#00d4aa]" /> Manage Problems
        </h1>
        <Link 
          href="/admin/problems/add"
          className="btn btn-primary flex items-center gap-2"
        >
          <PlusCircle className="w-5 h-5" /> Add Problem
        </Link>
      </div>

      <div className="bg-[#1a1f29] rounded-[15px] border border-[#2d3748] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-[#2d3748] text-[#a0aec0] text-sm uppercase tracking-wider">
                <th className="p-4 font-semibold">ID</th>
                <th className="p-4 font-semibold">Name</th>
                <th className="p-4 font-semibold">Short Code</th>
                <th className="p-4 font-semibold">Difficulty</th>
                <th className="p-4 font-semibold">Created At</th>
                <th className="p-4 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#2d3748]">
              {isLoading ? (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-gray-400">Loading problems...</td>
                </tr>
              ) : problems?.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-gray-400">No problems found.</td>
                </tr>
              ) : (
                problems?.map((problem) => (
                  <tr key={problem.id} className="hover:bg-white/5 transition-colors">
                    <td className="p-4 text-gray-400">#{problem.id}</td>
                    <td className="p-4 text-white font-medium">{problem.name}</td>
                    <td className="p-4 text-[#00d4aa] font-mono">{problem.shortCode}</td>
                    <td className="p-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
                        problem.difficulty === 'E' ? 'bg-green-400/20 text-green-400 border border-green-400' :
                        problem.difficulty === 'M' ? 'bg-yellow-400/20 text-yellow-400 border border-yellow-400' :
                        'bg-red-400/20 text-red-400 border border-red-400'
                      }`}>
                        {problem.difficulty === 'E' ? 'Easy' : problem.difficulty === 'M' ? 'Medium' : 'Hard'}
                      </span>
                    </td>
                    <td className="p-4 text-gray-400">
                      {format(new Date(problem.createdAt), "MMM d, yyyy")}
                    </td>
                    <td className="p-4 flex justify-end gap-2">
                      <Link 
                        href={`/admin/problems/${problem.shortCode}/edit`}
                        className="p-2 bg-[#17a2b8] text-white rounded hover:bg-[#138496] transition-colors"
                        title="Edit"
                      >
                        <Edit className="w-4 h-4" />
                      </Link>
                      <button 
                        onClick={() => handleDelete(problem.id)}
                        disabled={deleteMutation.isPending}
                        className="p-2 bg-[#dc3545] text-white rounded hover:bg-[#c82333] transition-colors disabled:opacity-50"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
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
