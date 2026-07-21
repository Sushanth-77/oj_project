"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import styles from "../admin.module.css";
import { formatDistanceToNow } from "date-fns";

export default function AdminDashboard() {
  const { data: analytics, isLoading } = useQuery({
    queryKey: ["adminAnalytics"],
    queryFn: async () => {
      const res = await fetch("/api/admin/analytics");
      if (!res.ok) throw new Error("Failed to fetch analytics");
      return res.json();
    },
  });

  if (isLoading) {
    return <div className="text-white text-center py-20">Loading dashboard...</div>;
  }

  // Calculate success rate based on mock or real data
  const acCount = analytics?.submissionsByVerdict?.find((v: any) => v.verdict === 'AC')?._count._all || 0;
  const totalSubs = analytics?.totalSubmissions || 0;
  const successRate = totalSubs > 0 ? Math.round((acCount / totalSubs) * 100) : 0;

  return (
    <>
      <div className={`${styles.alert} ${styles.alertInfo}`}>
        <strong>Welcome back, Admin!</strong> Here's an overview of your CodeMaster platform.
      </div>

      <div className={styles.statsGrid}>
        <div className={styles.statCard}>
          <span className={styles.statIcon}>📚</span>
          <span className={styles.statNumber}>{analytics?.totalProblems || 0}</span>
          <span className={styles.statLabel}>Total Problems</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statIcon}>📝</span>
          <span className={styles.statNumber}>{analytics?.totalSubmissions || 0}</span>
          <span className={styles.statLabel}>Submissions</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statIcon}>👥</span>
          <span className={styles.statNumber}>{analytics?.totalUsers || 0}</span>
          <span className={styles.statLabel}>Active Users</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statIcon}>✅</span>
          <span className={styles.statNumber}>{successRate}%</span>
          <span className={styles.statLabel}>Success Rate</span>
        </div>
      </div>

      <div className={styles.quickActions}>
        <Link href="/admin/problems/add" className={styles.actionCard}>
          <div className={styles.actionIcon}>➕</div>
          <div className={styles.actionTitle}>Add Problem</div>
          <div className={styles.actionDesc}>Create new coding challenges</div>
        </Link>
        <Link href="/admin/submissions" className={styles.actionCard}>
          <div className={styles.actionIcon}>👁️</div>
          <div className={styles.actionTitle}>View Submissions</div>
          <div className={styles.actionDesc}>Monitor user submissions</div>
        </Link>
        <Link href="/admin/users" className={styles.actionCard}>
          <div className={styles.actionIcon}>🔧</div>
          <div className={styles.actionTitle}>Manage Users</div>
          <div className={styles.actionDesc}>User administration</div>
        </Link>
      </div>

      <div className={styles.recentActivity}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionTitle}>
            <span>⚡</span> Recent Activity
          </h2>
        </div>

        {analytics?.recentSubmissions && analytics.recentSubmissions.length > 0 ? (
          analytics.recentSubmissions.slice(0, 5).map((submission: any) => (
            <div key={submission.id} className={styles.activityItem}>
              <div className={`${styles.activityIcon} ${submission.verdict === 'AC' ? styles.activityIconSuccess : styles.activityIconDanger}`}>
                {submission.verdict === 'AC' ? '✅' : '❌'}
              </div>
              <div className={styles.activityContent}>
                <div className={styles.activityTitle}>{submission.user?.name || submission.user?.email || 'A user'} submitted solution</div>
                <div className={styles.activityDesc}>
                  Problem "{submission.problem?.name}" - {submission.verdict}
                </div>
              </div>
              <div className={styles.activityTime}>{formatDistanceToNow(new Date(submission.submitted))} ago</div>
            </div>
          ))
        ) : (
          <div className={styles.activityItem}>
            <div className={`${styles.activityIcon} ${styles.activityIconInfo}`}>📝</div>
            <div className={styles.activityContent}>
              <div className={styles.activityTitle}>No recent submissions</div>
              <div className={styles.activityDesc}>No submission activity yet</div>
            </div>
            <div className={styles.activityTime}>-</div>
          </div>
        )}
      </div>
    </>
  );
}
