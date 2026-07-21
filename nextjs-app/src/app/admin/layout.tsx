"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { signOut, useSession } from "next-auth/react";
import styles from "./admin.module.css";

function getAdminTitle(pathname: string): string {
  if (pathname.includes("/problems/add")) return "Add Problem";
  if (pathname.includes("/problems/") && pathname.includes("/edit")) return "Edit Problem";
  if (pathname.startsWith("/admin/problems")) return "Manage Problems";
  if (pathname.startsWith("/admin/submissions")) return "All Submissions";
  if (pathname.startsWith("/admin/users")) return "Manage Users";
  if (pathname.startsWith("/admin/analytics")) return "Analytics";
  return "Dashboard Overview";
}

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const { data: session } = useSession();
  const title = getAdminTitle(pathname);

  return (
    <div className={styles.adminBody}>
      {/* Sidebar */}
      <nav className={styles.sidebar}>
        <div className={styles.logo}>
          <h2><span>💻</span> CodeMaster</h2>
        </div>
        <div className={styles.navMenu}>
          <Link href="/admin/dashboard" className={`${styles.navItem} ${pathname === '/admin/dashboard' ? styles.navItemActive : ''}`}>
            <i>📊</i> Dashboard
          </Link>
          <Link href="/admin/problems" className={`${styles.navItem} ${pathname.startsWith('/admin/problems') ? styles.navItemActive : ''}`}>
            <i>📚</i> Problems
          </Link>
          <Link href="/admin/submissions" className={`${styles.navItem} ${pathname === '/admin/submissions' ? styles.navItemActive : ''}`}>
            <i>📝</i> Submissions
          </Link>
          <Link href="/admin/users" className={`${styles.navItem} ${pathname === '/admin/users' ? styles.navItemActive : ''}`}>
            <i>👥</i> Users
          </Link>
          <Link href="/admin/analytics" className={`${styles.navItem} ${pathname === '/admin/analytics' ? styles.navItemActive : ''}`}>
            <i>📈</i> Analytics
          </Link>
        </div>
      </nav>

      {/* Main Content */}
      <main className={styles.mainContent}>
        {/* Header */}
        <header className={styles.header}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
            <h1 className={styles.headerTitle}>{title}</h1>
          </div>
          <div className={styles.headerActions}>
            <Link href="/problems" className={`${styles.btn} ${styles.btnSecondary}`}>
              <span>🏠</span> Main Site
            </Link>
            <Link href="/admin/problems/add" className={`${styles.btn} ${styles.btnPrimary}`}>
              <span>➕</span> Add Problem
            </Link>
            <button onClick={() => signOut({ callbackUrl: '/' })} className={`${styles.btn} ${styles.btnSecondary}`}>
              <span>🚪</span> Logout
            </button>
            <div className={styles.userMenu}>
              <div className={styles.userAvatar}>
                {session?.user?.name ? session.user.name.charAt(0).toUpperCase() : 'A'}
                <div className={styles.notificationDot}></div>
              </div>
            </div>
          </div>
        </header>

        {/* Dashboard Content Area */}
        <div className={styles.dashboardContent}>
          {children}
        </div>
      </main>
    </div>
  );
}

