import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { auth } from "@/lib/auth";

type RouteContext = { params: Promise<{ userId: string }> };

export async function GET(_req: Request, context: RouteContext) {
  try {
    const { userId } = await context.params;
    const session = await auth();

    const user = await prisma.user.findUnique({
      where: { id: userId },
      select: {
        id: true,
        name: true,
        email: true,
        image: true,
        createdAt: true,
        streak: true,
        userBadges: {
          include: { badge: true },
          orderBy: { awardedAt: "asc" },
        },
        submissions: {
          where: { verdict: "AC" },
          select: {
            problemId: true,
            submitted: true,
            problem: { select: { difficulty: true } },
          },
        },
      },
    });

    if (!user) {
      return NextResponse.json({ error: "User not found" }, { status: 404 });
    }

    // Unique AC problems
    const acProblemMap = new Map<number, { difficulty: string; submitted: Date }>();
    for (const sub of user.submissions) {
      if (!acProblemMap.has(sub.problemId)) {
        acProblemMap.set(sub.problemId, {
          difficulty: sub.problem.difficulty,
          submitted: sub.submitted,
        });
      }
    }

    const solvedProblems = Array.from(acProblemMap.values());
    const easyCount = solvedProblems.filter((p) => p.difficulty === "E").length;
    const mediumCount = solvedProblems.filter((p) => p.difficulty === "M").length;
    const hardCount = solvedProblems.filter((p) => p.difficulty === "H").length;
    const totalSolved = solvedProblems.length;
    const score = easyCount * 1 + mediumCount * 2 + hardCount * 3;

    // Total problems for solve rate
    const totalProblems = await prisma.problem.count();

    // Heatmap: count AC submissions per day (last 365 days)
    const yearAgo = new Date(Date.now() - 365 * 24 * 60 * 60 * 1000);
    const recentSubs = await prisma.submission.findMany({
      where: {
        userId,
        verdict: "AC",
        submitted: { gte: yearAgo },
      },
      select: { submitted: true },
    });

    const heatmap: Record<string, number> = {};
    for (const sub of recentSubs) {
      const dateStr = sub.submitted.toISOString().split("T")[0];
      heatmap[dateStr] = (heatmap[dateStr] ?? 0) + 1;
    }

    // Recent submissions (all verdicts, last 10)
    const recentSubmissions = await prisma.submission.findMany({
      where: { userId },
      orderBy: { submitted: "desc" },
      take: 10,
      include: {
        problem: { select: { name: true, shortCode: true, difficulty: true } },
      },
    });

    // Privacy: only show email if viewing own profile
    const isOwnProfile = session?.user?.id === userId;

    return NextResponse.json({
      user: {
        id: user.id,
        name: user.name,
        email: isOwnProfile ? user.email : null,
        image: user.image,
        createdAt: user.createdAt,
      },
      stats: {
        totalSolved,
        easyCount,
        mediumCount,
        hardCount,
        totalProblems,
        score,
        currentStreak: user.streak?.currentStreak ?? 0,
        longestStreak: user.streak?.longestStreak ?? 0,
      },
      badges: user.userBadges.map((ub) => ({
        slug: ub.badge.slug,
        name: ub.badge.name,
        description: ub.badge.description,
        icon: ub.badge.icon,
        awardedAt: ub.awardedAt,
      })),
      heatmap,
      recentSubmissions: recentSubmissions.map((s) => ({
        id: s.id,
        verdict: s.verdict,
        language: s.language,
        submitted: s.submitted,
        problem: s.problem,
      })),
    });
  } catch (error) {
    console.error("Profile error:", error);
    return NextResponse.json({ error: "Failed to fetch profile" }, { status: 500 });
  }
}
