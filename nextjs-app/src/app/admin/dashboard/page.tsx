"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import styles from "../admin.module.css";
import { formatDistanceToNow } from "date-fns";
import { VerdictBadge } from "@/components/ui/VerdictBadge";

const VERDICT_COLORS: Record<string, string> = {
  AC:  "#4ade80", WA: "#f87171", TLE: "#facc15",
  RE:  "#fb923c", CE: "#a78bfa", PE:  "#94a3b8", IE: "#64748b",
};

const LANG_COLORS: Record<string, string> = {
  python: "#60a5fa", cpp: "#c084fc", c: "#fb923c",
};

const DIFF_COLORS: Record<string, string> = { E: "#4ade80", M: "#facc15", H: "#f87171" };

function BarChart({ data, colors }: { data: { label: string; value: number }[]; colors: Record<string, string> }) {
  const max = Math.max(...data.map((d) => d.value), 1);
  return (
    <div className="space-y-2">
      {data.map((d) => (
        <div key={d.label} className="flex items-center gap-3">
          <span className="text-xs text-gray-400 w-12 text-right font-mono">{d.label}</span>
          <div className="flex-1 bg-[#0f1419] rounded-full h-5 overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500 flex items-center pl-2"
              style={{
                width: `${(d.value / max) * 100}%`,
                background: colors[d.label] || "#00d4aa",
                minWidth: d.value > 0 ? "2rem" : 0,
              }}
            >
              <span className="text-[10px] font-bold text-[#0f1419]">{d.value}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

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
    return (
      <div className="flex items-center justify-center py-20 gap-3 text-[#00d4aa]">
        <div className="w-5 h-5 border-2 border-t-transparent border-[#00d4aa] rounded-full animate-spin" />
        <span>Loading dashboard...</span>
      </div>
    );
  }

  const acCount = analytics?.submissionsByVerdict?.find((v: any) => v.verdict === "AC")?._count._all || 0;
  const totalSubs = analytics?.totalSubmissions || 0;
  const successRate = totalSubs > 0 ? Math.round((acCount / totalSubs) * 100) : 0;

  const verdictData = (analytics?.submissionsByVerdict ?? []).map((v: any) => ({
    label: v.verdict,
    value: v._count._all,
  }));

  const langData = (analytics?.submissionsByLanguage ?? []).map((l: any) => ({
    label: l.language,
    value: l._count._all,
  }));

  return (
    <>
      <div className={`${styles.alert} ${styles.alertInfo}`}>
        <strong>Welcome back, Admin!</strong> Here's an overview of your CodeMaster platform.
      </div>

      {/* Primary Stats Grid */}
      <div className={styles.statsGrid}>
        {[
          { icon: "📚", value: analytics?.totalProblems ?? 0, label: "Total Problems" },
          { icon: "📝", value: analytics?.totalSubmissions ?? 0, label: "Submissions" },
          { icon: "👥", value: analytics?.totalUsers ?? 0, label: "Total Users" },
          { icon: "✅", value: `${successRate}%`, label: "Success Rate" },
          { icon: "🔖", value: analytics?.totalBookmarks ?? 0, label: "Bookmarks" },
          { icon: "🏅", value: analytics?.totalBadgesAwarded ?? 0, label: "Badges Earned" },
        ].map((stat) => (
          <div key={stat.label} className={styles.statCard}>
            <span className={styles.statIcon}>{stat.icon}</span>
            <span className={styles.statNumber}>{stat.value}</span>
            <span className={styles.statLabel}>{stat.label}</span>
          </div>
        ))}
      </div>

      {/* Charts row */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem", marginBottom: "1.5rem" }}>
        {/* Verdict breakdown */}
        <div style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "12px", padding: "1.25rem" }}>
          <h3 style={{ color: "white", fontSize: "0.85rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: "1rem" }}>
            ⚡ Verdict Breakdown
          </h3>
          <BarChart data={verdictData} colors={VERDICT_COLORS} />
        </div>
        {/* Language breakdown */}
        <div style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "12px", padding: "1.25rem" }}>
          <h3 style={{ color: "white", fontSize: "0.85rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: "1rem" }}>
            💻 Language Breakdown
          </h3>
          <BarChart data={langData} colors={LANG_COLORS} />
        </div>
      </div>

      {/* Top solvers + Popular problems */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem", marginBottom: "1.5rem" }}>
        {/* Top solvers */}
        <div style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "12px", padding: "1.25rem" }}>
          <h3 style={{ color: "white", fontSize: "0.85rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: "1rem" }}>
            🏆 Top Solvers
          </h3>
          <div className="space-y-2">
            {(analytics?.topSolvers ?? []).map((s: any, i: number) => (
              <div key={s.userId} style={{ display: "flex", alignItems: "center", gap: "0.75rem", padding: "0.5rem", borderRadius: "8px", background: "rgba(0,212,170,0.03)" }}>
                <span style={{ color: i === 0 ? "#facc15" : i === 1 ? "#d1d5db" : i === 2 ? "#d97706" : "#6b7280", fontWeight: 700, fontSize: "0.8rem", width: "1.2rem" }}>
                  #{i + 1}
                </span>
                <Link href={`/profile/${s.userId}`} style={{ color: "#00d4aa", fontSize: "0.85rem", fontWeight: 600, flex: 1 }} className="hover:underline">
                  {s.user?.name || s.user?.email?.split("@")[0] || "User"}
                </Link>
                <span style={{ color: "#4ade80", fontSize: "0.8rem", fontWeight: 700 }}>{s._count._all} AC</span>
              </div>
            ))}
            {(analytics?.topSolvers ?? []).length === 0 && (
              <p style={{ color: "#6b7280", fontSize: "0.85rem" }}>No solved submissions yet.</p>
            )}
          </div>
        </div>

        {/* Most attempted problems */}
        <div style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "12px", padding: "1.25rem" }}>
          <h3 style={{ color: "white", fontSize: "0.85rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: "1rem" }}>
            🔥 Most Attempted
          </h3>
          <div className="space-y-2">
            {(analytics?.popularProblems ?? []).map((p: any) => (
              <div key={p.problemId} style={{ display: "flex", alignItems: "center", gap: "0.75rem", padding: "0.5rem", borderRadius: "8px" }}>
                <Link href={`/problems/${p.problem?.shortCode}`} style={{ color: "#e2e8f0", fontSize: "0.85rem", flex: 1 }} className="hover:text-[#00d4aa] transition-colors">
                  {p.problem?.name || `Problem #${p.problemId}`}
                </Link>
                <span style={{ color: DIFF_COLORS[p.problem?.difficulty] || "#94a3b8", fontSize: "0.7rem", fontWeight: 700 }}>
                  {p.problem?.difficulty === "E" ? "Easy" : p.problem?.difficulty === "M" ? "Medium" : "Hard"}
                </span>
                <span style={{ color: "#94a3b8", fontSize: "0.8rem" }}>{p._count._all}</span>
              </div>
            ))}
            {(analytics?.popularProblems ?? []).length === 0 && (
              <p style={{ color: "#6b7280", fontSize: "0.85rem" }}>No submissions yet.</p>
            )}
          </div>
        </div>
      </div>

      {/* Quick actions */}
      <div className={styles.quickActions}>
        <Link href="/admin/problems/add" className={styles.actionCard}>
          <div className={styles.actionIcon}>➕</div>
          <div className={styles.actionTitle}>Add Problem</div>
          <div className={styles.actionDesc}>Create new coding challenges</div>
        </Link>
        <Link href="/admin/submissions" className={styles.actionCard}>
          <div className={styles.actionIcon}>👁️</div>
          <div className={styles.actionTitle}>All Submissions</div>
          <div className={styles.actionDesc}>Monitor user submissions</div>
        </Link>
        <Link href="/admin/users" className={styles.actionCard}>
          <div className={styles.actionIcon}>🔧</div>
          <div className={styles.actionTitle}>Manage Users</div>
          <div className={styles.actionDesc}>User administration</div>
        </Link>
        <Link href="/leaderboard" className={styles.actionCard}>
          <div className={styles.actionIcon}>🏆</div>
          <div className={styles.actionTitle}>Leaderboard</div>
          <div className={styles.actionDesc}>View public rankings</div>
        </Link>
      </div>

      {/* Recent Submissions */}
      <div className={styles.recentActivity}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionTitle}>
            <span>⚡</span> Recent Submissions
          </h2>
        </div>
        {analytics?.recentSubmissions && analytics.recentSubmissions.length > 0 ? (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  {["User", "Problem", "Language", "Verdict", "Time"].map((h) => (
                    <th key={h} style={{ padding: "0.5rem 0.75rem", textAlign: "left", fontSize: "0.7rem", color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.1em", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {analytics.recentSubmissions.map((sub: any) => (
                  <tr key={sub.id} style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
                    <td style={{ padding: "0.6rem 0.75rem" }}>
                      <Link href={`/profile/${sub.user?.id}`} style={{ color: "#00d4aa", fontSize: "0.85rem" }} className="hover:underline">
                        {sub.user?.name || sub.user?.email?.split("@")[0] || "—"}
                      </Link>
                    </td>
                    <td style={{ padding: "0.6rem 0.75rem" }}>
                      <Link href={`/problems/${sub.problem?.shortCode}`} style={{ color: "#e2e8f0", fontSize: "0.85rem" }} className="hover:text-[#00d4aa]">
                        {sub.problem?.name}
                      </Link>
                    </td>
                    <td style={{ padding: "0.6rem 0.75rem" }}>
                      <span style={{ background: "rgba(255,255,255,0.06)", padding: "0.15rem 0.5rem", borderRadius: "4px", fontSize: "0.75rem", color: "#94a3b8" }}>
                        {sub.language}
                      </span>
                    </td>
                    <td style={{ padding: "0.6rem 0.75rem" }}>
                      <VerdictBadge verdict={sub.verdict} />
                    </td>
                    <td style={{ padding: "0.6rem 0.75rem", color: "#6b7280", fontSize: "0.8rem" }}>
                      {formatDistanceToNow(new Date(sub.submitted), { addSuffix: true })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className={styles.activityItem}>
            <div className={`${styles.activityIcon} ${styles.activityIconInfo}`}>📝</div>
            <div className={styles.activityContent}>
              <div className={styles.activityTitle}>No recent submissions</div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
