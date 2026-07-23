import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";

type RouteContext = { params: Promise<{ shortCode: string }> };

export async function GET(_req: Request, context: RouteContext) {
  try {
    const { shortCode } = await context.params;
    const problem = await prisma.problem.findUnique({
      where: { shortCode },
      select: { id: true },
    });

    if (!problem) {
      return NextResponse.json({ error: "Problem not found" }, { status: 404 });
    }

    // Count total submissions and AC submissions
    const [total, accepted] = await Promise.all([
      prisma.submission.count({ where: { problemId: problem.id } }),
      prisma.submission.count({ where: { problemId: problem.id, verdict: "AC" } }),
    ]);

    // Language breakdown (only for AC submissions)
    const langGroups = await prisma.submission.groupBy({
      by: ["language"],
      where: { problemId: problem.id },
      _count: { language: true },
      orderBy: { _count: { language: "desc" } },
    });

    const acceptanceRate = total > 0 ? Math.round((accepted / total) * 100) : 0;

    return NextResponse.json({
      total,
      accepted,
      acceptanceRate,
      languageBreakdown: langGroups.map((g) => ({
        language: g.language,
        count: g._count.language,
      })),
    });
  } catch (error) {
    console.error("Problem stats error:", error);
    return NextResponse.json({ error: "Failed to fetch stats" }, { status: 500 });
  }
}
