import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { auth } from "@/lib/auth";

type RouteContext = { params: Promise<{ id: string }> };

// GET /api/contests/[id] — contest details with problems and live scoreboard
export async function GET(_req: Request, context: RouteContext) {
  try {
    const { id } = await context.params;
    const contestId = parseInt(id);
    if (isNaN(contestId)) return NextResponse.json({ error: "Invalid ID" }, { status: 400 });

    const session = await auth();
    const now = new Date();

    const contest = await prisma.contest.findUnique({
      where: { id: contestId },
      include: {
        problems: {
          orderBy: { order: "asc" },
          include: {
            problem: {
              select: { id: true, name: true, shortCode: true, difficulty: true },
            },
          },
        },
        _count: { select: { registrations: true } },
      },
    });

    if (!contest) return NextResponse.json({ error: "Not found" }, { status: 404 });
    if (!contest.isPublished && !session?.user?.isAdmin) {
      return NextResponse.json({ error: "Not found" }, { status: 404 });
    }

    const isLive = now >= contest.startsAt && now <= contest.endsAt;
    const isPast = now > contest.endsAt;
    const status = now < contest.startsAt ? "upcoming" : isLive ? "live" : "past";

    // Check if current user is registered
    let isRegistered = false;
    if (session?.user?.id) {
      const reg = await prisma.contestRegistration.findUnique({
        where: { contestId_userId: { contestId, userId: session.user.id } },
      });
      isRegistered = !!reg;
    }

    // Build scoreboard for live/past contests
    let scoreboard: any[] = [];
    if (isLive || isPast) {
      const registrations = await prisma.contestRegistration.findMany({
        where: { contestId },
        include: { user: { select: { id: true, name: true, image: true, email: true } } },
      });

      const problemIds = contest.problems.map((cp) => cp.problemId);
      const contestProblemPoints = new Map(contest.problems.map((cp) => [cp.problemId, cp.points]));

      // Get AC submissions during contest window for registered users
      const userIds = registrations.map((r) => r.userId);
      const acSubmissions = await prisma.submission.findMany({
        where: {
          userId: { in: userIds },
          problemId: { in: problemIds },
          verdict: "AC",
          submitted: { gte: contest.startsAt, lte: contest.endsAt },
        },
        select: { userId: true, problemId: true, submitted: true },
        distinct: ["userId", "problemId"],
      });

      // Build score map
      const scoreMap = new Map<string, { score: number; solved: number }>();
      for (const sub of acSubmissions) {
        const current = scoreMap.get(sub.userId) || { score: 0, solved: 0 };
        const pts = contestProblemPoints.get(sub.problemId) || 100;
        scoreMap.set(sub.userId, { score: current.score + pts, solved: current.solved + 1 });
      }

      scoreboard = registrations
        .map((r) => {
          const stats = scoreMap.get(r.userId) || { score: 0, solved: 0 };
          return {
            userId: r.userId,
            name: r.user.name,
            image: r.user.image,
            email: r.user.email,
            ...stats,
          };
        })
        .sort((a, b) => b.score - a.score || b.solved - a.solved)
        .map((entry, idx) => ({ ...entry, rank: idx + 1 }));
    }

    return NextResponse.json({
      ...contest,
      status,
      registrationCount: contest._count.registrations,
      isRegistered,
      scoreboard,
      _count: undefined,
    });
  } catch (error) {
    console.error("Contest GET error:", error);
    return NextResponse.json({ error: "Server error" }, { status: 500 });
  }
}
