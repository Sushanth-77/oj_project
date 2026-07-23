"use client";

import Link from "next/link";
import { useSession, signOut } from "next-auth/react";
import { usePathname } from "next/navigation";
import { Code, ChevronDown, History, LogOut, Trophy, User } from "lucide-react";
import { useState, useEffect, useRef } from "react";

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

          <div className="flex items-center">
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
