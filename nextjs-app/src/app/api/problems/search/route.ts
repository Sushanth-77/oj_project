import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { auth } from "@/lib/auth";

// GET /api/problems/search — full-text search with filters
export async function GET(request: Request) {
  try {
    const session = await auth();
    const { searchParams } = new URL(request.url);

    const q = searchParams.get("q") || "";
    const difficulty = searchParams.get("difficulty"); // E, M, H or null
    const topic = searchParams.get("topic") || "";
    const sortBy = searchParams.get("sortBy") || "newest"; // newest, acceptance, attempts
    const page = parseInt(searchParams.get("page") || "1");
    const limit = 20;

    // Build where clause
    const where: any = {};
    if (q) {
      where.OR = [
        { name: { contains: q, mode: "insensitive" } },
        { topics: { hasSome: [q] } },
      ];
    }
    if (difficulty && ["E", "M", "H"].includes(difficulty)) {
      where.difficulty = difficulty;
    }
    if (topic) {
      where.topics = { has: topic };
    }

    // Build orderBy
    let orderBy: any = { createdAt: "desc" };
    if (sortBy === "attempts") {
      orderBy = { submissions: { _count: "desc" } };
    }

    const [problems, total] = await Promise.all([
      prisma.problem.findMany({
        where,
        orderBy,
        skip: (page - 1) * limit,
        take: limit,
        select: {
          id: true,
          name: true,
          shortCode: true,
          difficulty: true,
          topics: true,
          createdAt: true,
          _count: { select: { submissions: true } },
        },
      }),
      prisma.problem.count({ where }),
    ]);

    // Get acceptance rates in one query
    const problemIds = problems.map((p) => p.id);
    const acCounts = await prisma.submission.groupBy({
      by: ["problemId"],
      where: { problemId: { in: problemIds }, verdict: "AC" },
      _count: true,
    });
    const totalCounts = await prisma.submission.groupBy({
      by: ["problemId"],
      where: { problemId: { in: problemIds } },
      _count: true,
    });

    const acMap = new Map(acCounts.map((r) => [r.problemId, r._count]));
    const totalMap = new Map(totalCounts.map((r) => [r.problemId, r._count]));

    // Get solved status for logged-in users
    let solvedSet = new Set<number>();
    if (session?.user?.id) {
      const solved = await prisma.submission.findMany({
        where: { userId: session.user.id, verdict: "AC", problemId: { in: problemIds } },
        select: { problemId: true },
        distinct: ["problemId"],
      });
      solvedSet = new Set(solved.map((s) => s.problemId));
    }

    const enriched = problems.map((p) => {
      const ac = acMap.get(p.id) || 0;
      const total = totalMap.get(p.id) || 0;
      const acceptanceRate = total > 0 ? Math.round((ac / total) * 100) : 0;
      return {
        ...p,
        submissionCount: p._count.submissions,
        acceptanceRate,
        solved: solvedSet.has(p.id),
        _count: undefined,
      };
    });

    // Sort by acceptance rate if needed (done client-side from DB result)
    if (sortBy === "acceptance") {
      enriched.sort((a, b) => b.acceptanceRate - a.acceptanceRate);
    }

    return NextResponse.json({
      problems: enriched,
      total,
      pages: Math.ceil(total / limit),
    });
  } catch (error) {
    console.error("Search GET error:", error);
    return NextResponse.json({ error: "Server error" }, { status: 500 });
  }
}
