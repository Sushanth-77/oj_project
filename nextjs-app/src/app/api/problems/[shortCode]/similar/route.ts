import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { auth } from "@/lib/auth";

type RouteContext = { params: Promise<{ shortCode: string }> };

// GET /api/problems/[shortCode]/similar — returns 3 problems with overlapping topics
export async function GET(_req: Request, context: RouteContext) {
  try {
    const { shortCode } = await context.params;
    const session = await auth();

    const problem = await prisma.problem.findUnique({
      where: { shortCode },
      select: { id: true, topics: true, difficulty: true },
    });
    if (!problem) return NextResponse.json({ similar: [] });

    // Get already-solved problem IDs to exclude
    let solvedIds: number[] = [];
    if (session?.user?.id) {
      const solved = await prisma.submission.findMany({
        where: { userId: session.user.id, verdict: "AC" },
        select: { problemId: true },
        distinct: ["problemId"],
      });
      solvedIds = solved.map((s) => s.problemId);
    }

    // Find problems with at least 1 overlapping topic
    const similar = await prisma.problem.findMany({
      where: {
        id: { not: problem.id, notIn: solvedIds },
        topics: { hasSome: problem.topics },
      },
      select: {
        id: true,
        name: true,
        shortCode: true,
        difficulty: true,
        topics: true,
      },
      take: 6,
    });

    // Score by number of overlapping topics, then take top 3
    const scored = similar
      .map((p) => ({
        ...p,
        overlap: p.topics.filter((t) => problem.topics.includes(t)).length,
      }))
      .sort((a, b) => b.overlap - a.overlap)
      .slice(0, 3);

    return NextResponse.json({ similar: scored });
  } catch (error) {
    console.error("Similar problems GET error:", error);
    return NextResponse.json({ similar: [] });
  }
}
