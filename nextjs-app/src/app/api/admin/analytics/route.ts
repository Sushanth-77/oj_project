import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/db";

export async function GET() {
  try {
    const session = await auth();
    if (!session?.user?.isAdmin) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const [
      totalUsers,
      totalProblems,
      totalSubmissions,
      totalBookmarks,
      totalBadgesAwarded,
      submissionsByVerdict,
      submissionsByLanguage,
      recentSubmissions,
      topSolvers,
      hardestProblems,
    ] = await Promise.all([
      prisma.user.count(),
      prisma.problem.count(),
      prisma.submission.count(),
      prisma.bookmark.count(),
      prisma.userBadge.count(),
      prisma.submission.groupBy({ by: ["verdict"], _count: { _all: true } }),
      prisma.submission.groupBy({ by: ["language"], _count: { _all: true } }),
      prisma.submission.findMany({
        take: 8,
        orderBy: { submitted: "desc" },
        include: {
          user: { select: { name: true, email: true, id: true } },
          problem: { select: { name: true, shortCode: true } },
        },
      }),
      // Top 5 users by AC count
      prisma.submission.groupBy({
        by: ["userId"],
        where: { verdict: "AC" },
        _count: { _all: true },
        orderBy: { _count: { id: "desc" } },
        take: 5,
      }),
      // Problems with highest submission counts
      prisma.submission.groupBy({
        by: ["problemId"],
        _count: { _all: true },
        orderBy: { _count: { id: "desc" } },
        take: 5,
      }),
    ]);

    // Enrich top solvers with user info
    const topSolverIds = topSolvers.map((s) => s.userId);
    const solverUsers = await prisma.user.findMany({
      where: { id: { in: topSolverIds } },
      select: { id: true, name: true, email: true },
    });
    const topSolversEnriched = topSolvers.map((s) => ({
      ...s,
      user: solverUsers.find((u) => u.id === s.userId),
    }));

    // Enrich hardest problems with name
    const problemIds = hardestProblems.map((p) => p.problemId);
    const problemDetails = await prisma.problem.findMany({
      where: { id: { in: problemIds } },
      select: { id: true, name: true, shortCode: true, difficulty: true },
    });
    const hardestEnriched = hardestProblems.map((p) => ({
      ...p,
      problem: problemDetails.find((d) => d.id === p.problemId),
    }));

    return NextResponse.json({
      totalUsers,
      totalProblems,
      totalSubmissions,
      totalBookmarks,
      totalBadgesAwarded,
      submissionsByVerdict,
      submissionsByLanguage,
      recentSubmissions,
      topSolvers: topSolversEnriched,
      popularProblems: hardestEnriched,
    });
  } catch (error) {
    console.error("Failed to fetch analytics:", error);
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}
