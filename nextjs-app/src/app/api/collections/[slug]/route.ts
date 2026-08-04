import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { auth } from "@/lib/auth";

type RouteContext = { params: Promise<{ slug: string }> };

// GET /api/collections/[slug] — get single collection with problems + user progress
export async function GET(_req: Request, context: RouteContext) {
  try {
    const { slug } = await context.params;
    const session = await auth();

    const collection = await prisma.collection.findUnique({
      where: { slug },
      include: {
        problems: {
          orderBy: { order: "asc" },
          include: {
            problem: {
              select: {
                id: true,
                name: true,
                shortCode: true,
                difficulty: true,
                topics: true,
              },
            },
          },
        },
      },
    });

    if (!collection) return NextResponse.json({ error: "Not found" }, { status: 404 });
    if (!collection.isPublished && !session?.user?.isAdmin) {
      return NextResponse.json({ error: "Not found" }, { status: 404 });
    }

    // If logged in, mark which problems are solved
    let solvedSet = new Set<number>();
    if (session?.user?.id) {
      const solved = await prisma.submission.findMany({
        where: { userId: session.user.id, verdict: "AC" },
        select: { problemId: true },
        distinct: ["problemId"],
      });
      solvedSet = new Set(solved.map((s) => s.problemId));
    }

    return NextResponse.json({
      ...collection,
      problems: collection.problems.map((cp) => ({
        ...cp,
        solved: solvedSet.has(cp.problemId),
      })),
    });
  } catch (error) {
    console.error("Collection GET error:", error);
    return NextResponse.json({ error: "Server error" }, { status: 500 });
  }
}
