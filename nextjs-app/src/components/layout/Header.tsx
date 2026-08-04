"use client";

import Link from "next/link";
import { useSession, signOut } from "next-auth/react";
import { usePathname } from "next/navigation";
import { Code, ChevronDown, History, LogOut, Trophy, User, Bell, X, Check } from "lucide-react";
import { useState, useEffect, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { formatDistanceToNow } from "date-fns";

interface Notification {
  id: number;
  type: string;
  title: string;
  message: string;
  link: string | null;
  read: boolean;
  createdAt: string;
}

function NotificationBell() {
  const { data: session } = useSession();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();

  const { data } = useQuery<{ notifications: Notification[]; unreadCount: number }>({
    queryKey: ["notifications"],
    queryFn: async () => {
      const res = await fetch("/api/notifications?limit=10");
      if (!res.ok) return { notifications: [], unreadCount: 0 };
      return res.json();
    },
    enabled: !!session,
    refetchInterval: 30_000,
    staleTime: 20_000,
  });

  const markAllRead = useMutation({
    mutationFn: async () => {
      await fetch("/api/notifications", { method: "PATCH" });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  const markOneRead = useMutation({
    mutationFn: async (id: number) => {
      await fetch(`/api/notifications/${id}`, { method: "PATCH" });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    if (open) document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  if (!session) return null;

  const unreadCount = data?.unreadCount ?? 0;
  const notifications = data?.notifications ?? [];

  const notifIcon: Record<string, string> = {
    badge: "🏅",
    xp_levelup: "🎉",
    daily: "🎯",
    announcement: "📢",
    reply: "💬",
  };

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((v) => !v)}
        className="relative p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-all"
        title="Notifications"
      >
        <Bell className="w-5 h-5" />
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-[#00d4aa] text-[#0f1419] text-[10px] font-bold rounded-full flex items-center justify-center">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-80 bg-[#1a1f29] border border-[#2d3748] rounded-xl shadow-2xl z-50 overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-[#2d3748]">
            <span className="text-white font-semibold text-sm">Notifications</span>
            <div className="flex items-center gap-2">
              {unreadCount > 0 && (
                <button
                  onClick={() => markAllRead.mutate()}
                  className="text-xs text-[#00d4aa] hover:text-[#00b38f] flex items-center gap-1"
                >
                  <Check className="w-3 h-3" />
                  Mark all read
                </button>
              )}
              <button onClick={() => setOpen(false)} className="text-gray-500 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="max-h-80 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="px-4 py-8 text-center text-gray-500 text-sm">
                <Bell className="w-8 h-8 mx-auto mb-2 opacity-40" />
                No notifications yet
              </div>
            ) : (
              notifications.map((n) => (
                <div
                  key={n.id}
                  onClick={() => {
                    if (!n.read) markOneRead.mutate(n.id);
                    if (n.link) window.location.href = n.link;
                    setOpen(false);
                  }}
                  className={`flex items-start gap-3 px-4 py-3 border-b border-[#2d3748]/50 cursor-pointer transition-colors hover:bg-white/5 ${
                    !n.read ? "bg-[#00d4aa]/5" : ""
                  }`}
                >
                  <span className="text-xl mt-0.5 flex-shrink-0">{notifIcon[n.type] ?? "📣"}</span>
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm font-semibold truncate ${!n.read ? "text-white" : "text-gray-300"}`}>
                      {n.title}
                    </p>
                    <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{n.message}</p>
                    <p className="text-xs text-gray-600 mt-1">
                      {formatDistanceToNow(new Date(n.createdAt), { addSuffix: true })}
                    </p>
                  </div>
                  {!n.read && (
                    <div className="w-2 h-2 bg-[#00d4aa] rounded-full mt-1.5 flex-shrink-0" />
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export function Header() {
  const { data: session } = useSession();
  const pathname = usePathname();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    };
    if (dropdownOpen) {
      document.addEventListener("mousedown", handleOutsideClick);
    }
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, [dropdownOpen]);

  // Hide header on auth pages and admin pages (admin has its own layout)
  if (pathname.startsWith("/login") || pathname.startsWith("/register") || pathname.startsWith("/admin")) {
    return null;
  }

  const navLink = (href: string, label: string) => (
    <Link
      href={href}
      className={`${
        pathname.startsWith(href)
          ? "text-[#00d4aa] border-b-2 border-[#00d4aa]"
          : "text-gray-300 hover:text-white"
      } px-1 py-5 text-sm font-medium transition-colors`}
    >
      {label}
    </Link>
  );

  return (
    <header className="sticky top-0 z-50 bg-[#1a1f29] border-b border-[#2d3748] shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <Link href="/" className="flex items-center gap-2 text-[#00d4aa] font-bold text-xl hover:opacity-90">
              <Code className="h-6 w-6" />
              <span>CodeMaster</span>
            </Link>

            <nav className="hidden md:flex ml-10 space-x-8">
              {navLink("/problems", "Problems")}
              {navLink("/leaderboard", "Leaderboard")}
              {navLink("/contests", "Contests")}
              {navLink("/collections", "Collections")}
              {session && navLink("/submissions", "My Submissions")}
            </nav>

            {session?.user?.isAdmin && (
              <div className="hidden md:flex items-center ml-6 pl-6 border-l border-[#2d3748]">
                <span className="text-red-500 font-bold text-xs mr-4">ADMIN:</span>
                <Link href="/admin/dashboard" className="text-red-400 hover:text-red-300 text-sm font-medium">
                  Dashboard
                </Link>
              </div>
            )}
          </div>

          <div className="flex items-center gap-2">
            {/* Notification Bell */}
            <NotificationBell />

            {session ? (
              <div className="relative" ref={dropdownRef}>
                <button
                  onClick={() => setDropdownOpen(!dropdownOpen)}
                  className="flex items-center gap-2 text-gray-300 hover:text-white focus:outline-none"
                >
                  <div className="h-8 w-8 rounded-full bg-gradient-to-br from-[#00d4aa] to-[#00b894] flex items-center justify-center text-white font-bold text-sm">
                    {session.user?.name?.[0]?.toUpperCase() || session.user?.email?.[0]?.toUpperCase()}
                  </div>
                  <span className="text-sm font-medium hidden sm:block">{session.user?.name || session.user?.email}</span>
                  <ChevronDown className="h-4 w-4" />
                </button>

                {dropdownOpen && (
                  <div className="absolute right-0 mt-2 w-52 rounded-md shadow-lg bg-[#2d3748] ring-1 ring-black ring-opacity-5 py-1">
                    <Link
                      href={`/profile/${session.user?.id}`}
                      className="flex items-center px-4 py-2 text-sm text-gray-200 hover:bg-[#1a1f29]"
                      onClick={() => setDropdownOpen(false)}
                    >
                      <User className="h-4 w-4 mr-2" />
                      My Profile
                    </Link>
                    <Link
                      href="/submissions"
                      className="flex items-center px-4 py-2 text-sm text-gray-200 hover:bg-[#1a1f29]"
                      onClick={() => setDropdownOpen(false)}
                    >
                      <History className="h-4 w-4 mr-2" />
                      My Submissions
                    </Link>
                    <Link
                      href="/leaderboard"
                      className="flex items-center px-4 py-2 text-sm text-gray-200 hover:bg-[#1a1f29]"
                      onClick={() => setDropdownOpen(false)}
                    >
                      <Trophy className="h-4 w-4 mr-2" />
                      Leaderboard
                    </Link>
                    <div className="border-t border-[#1a1f29] my-1" />
                    <button
                      onClick={() => signOut({ callbackUrl: "/login" })}
                      className="flex items-center w-full text-left px-4 py-2 text-sm text-gray-200 hover:bg-[#1a1f29]"
                    >
                      <LogOut className="h-4 w-4 mr-2" />
                      Logout
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex space-x-4">
                <Link
                  href="/login"
                  className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium"
                >
                  Login
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
