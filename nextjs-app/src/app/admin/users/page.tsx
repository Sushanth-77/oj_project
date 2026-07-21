"use client";

import { useQuery } from "@tanstack/react-query";
import { Users, Shield, User } from "lucide-react";
import { format } from "date-fns";

export default function AdminUsersList() {
  const { data: users, isLoading } = useQuery({
    queryKey: ["adminUsers"],
    queryFn: async () => {
      const res = await fetch("/api/admin/users");
      if (!res.ok) throw new Error("Failed to fetch users");
      return res.json();
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center bg-[#1a1f29] p-6 rounded-[15px] border border-[#2d3748]">
        <h1 className="text-2xl font-bold text-white flex items-center gap-3">
          <Users className="text-[#00d4aa]" /> Manage Users
        </h1>
      </div>

      <div className="bg-[#1a1f29] rounded-[15px] border border-[#2d3748] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-[#2d3748] text-[#a0aec0] text-sm uppercase tracking-wider">
                <th className="p-4 font-semibold">User</th>
                <th className="p-4 font-semibold">Email</th>
                <th className="p-4 font-semibold">Role</th>
                <th className="p-4 font-semibold">Submissions</th>
                <th className="p-4 font-semibold">Joined At</th>
                <th className="p-4 font-semibold">Last Login</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#2d3748]">
              {isLoading ? (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-gray-400">Loading users...</td>
                </tr>
              ) : users?.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-gray-400">No users found.</td>
                </tr>
              ) : (
                users?.map((user: any) => (
                  <tr key={user.id} className="hover:bg-white/5 transition-colors">
                    <td className="p-4">
                      <div className="flex items-center gap-3">
                        {user.image ? (
                          <img src={user.image} alt={user.name} className="w-8 h-8 rounded-full" />
                        ) : (
                          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#00d4aa] to-[#00b894] flex items-center justify-center text-white font-bold text-sm">
                            {user.name?.[0]?.toUpperCase() || user.email?.[0]?.toUpperCase()}
                          </div>
                        )}
                        <span className="text-white font-medium">{user.name || "Unknown"}</span>
                      </div>
                    </td>
                    <td className="p-4 text-gray-300">{user.email}</td>
                    <td className="p-4">
                      {user.isAdmin ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-red-500/10 text-red-500 border border-red-500/20">
                          <Shield className="w-3 h-3" /> Admin
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-blue-500/10 text-blue-500 border border-blue-500/20">
                          <User className="w-3 h-3" /> User
                        </span>
                      )}
                    </td>
                    <td className="p-4 text-gray-300 font-mono">
                      {user._count?.submissions || 0}
                    </td>
                    <td className="p-4 text-gray-400 text-sm">
                      {format(new Date(user.createdAt), "MMM d, yyyy")}
                    </td>
                    <td className="p-4 text-gray-400 text-sm">
                      {user.lastLogin ? format(new Date(user.lastLogin), "MMM d, yyyy") : "Never"}
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
