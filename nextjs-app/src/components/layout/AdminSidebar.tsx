"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  Code, 
  LayoutDashboard, 
  List, 
  PlusCircle, 
  History, 
  Users, 
  BarChart,
  LogOut
} from "lucide-react";
import { signOut } from "next-auth/react";

export function AdminSidebar() {
  const pathname = usePathname();

  const navItems = [
    { name: "Dashboard", href: "/admin/dashboard", icon: LayoutDashboard },
    { name: "Manage Problems", href: "/admin/problems", icon: List },
    { name: "Add Problem", href: "/admin/problems/add", icon: PlusCircle },
    { name: "All Submissions", href: "/admin/submissions", icon: History },
    { name: "Users", href: "/admin/users", icon: Users },
  ];

  return (
    <div className="w-[280px] h-screen fixed left-0 top-0 bg-gradient-to-b from-[#1a1f29] to-[#0f1419] border-r border-[#2d3748] z-50 flex flex-col">
      <div className="p-[30px_25px] border-b border-[#2d3748]">
        <Link href="/" className="flex items-center gap-2 text-[#00d4aa] font-bold text-2xl hover:opacity-90">
          <Code className="h-7 w-7" />
          <span>CodeMaster</span>
        </Link>
      </div>

      <div className="flex-1 py-5 overflow-y-auto">
        <nav className="space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href || (pathname.startsWith(item.href) && item.href !== '/admin/dashboard');
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center px-[25px] py-[15px] text-sm transition-all duration-300 border-l-4 ${
                  isActive
                    ? "bg-[rgba(0,212,170,0.1)] text-[#00d4aa] border-[#00d4aa] translate-x-[5px]"
                    : "text-[#a0aec0] border-transparent hover:bg-[rgba(0,212,170,0.1)] hover:text-[#00d4aa] hover:border-[#00d4aa] hover:translate-x-[5px]"
                }`}
              >
                <item.icon className="h-5 w-5 mr-[15px]" />
                {item.name}
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="p-4 border-t border-[#2d3748]">
        <button
          onClick={() => signOut({ callbackUrl: "/login" })}
          className="flex items-center w-full px-[25px] py-[15px] text-sm text-[#a0aec0] hover:text-white transition-colors"
        >
          <LogOut className="h-5 w-5 mr-[15px]" />
          Logout
        </button>
      </div>
    </div>
  );
}
