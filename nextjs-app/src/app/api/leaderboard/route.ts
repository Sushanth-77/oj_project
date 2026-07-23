import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { auth } from "@/lib/auth";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const range = searchParams.get("range") || "all"; // "all" | "week"

    const since = range === "week"
      ? new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
      : new Date(0);

    // Get all AC submissions within range, with problem difficulty
    const acSubmissions = await prisma.submission.findMany({
      where: {
        verdict: "AC",
        submitted: { gte: since },
      },
      select: {
        userId: true,
        problemId: true,
        problem: { select: { difficulty: true } },
        user: { select: { id: true, name: true, email: true, image: true, createdAt: true } },
      },
    });

    // Compute per-user: distinct problems solved + weighted score
    const userMap = new Map<string, {
      userId: string;
      name: string | null;
      email: string;
      image: string | null;
      solvedProblems: Set<number>;
      score: number;
      easyCount: number;
      mediumCount: number;
      hardCount: number;
    }>();

    for (const sub of acSubmissions) {
      const uid = sub.userId;
      if (!userMap.has(uid)) {
        userMap.set(uid, {
          userId: uid,
          name: sub.user.name,
          email: sub.user.email,
          image: sub.user.image,
          solvedProblems: new Set(),
          score: 0,
          easyCount: 0,
          mediumCount: 0,
          hardCount: 0,
        });
      }
      const entry = userMap.get(uid)!;
      // Only count each problem once per user
      if (!entry.solvedProblems.has(sub.problemId)) {
        entry.solvedProblems.add(sub.problemId);
        const diff = sub.problem.difficulty;
        const pts = diff === "H" ? 3 : diff === "M" ? 2 : 1;
        entry.score += pts;
        if (diff === "E") entry.easyCount++;
        else if (diff === "M") entry.mediumCount++;
        else if (diff === "H") entry.hardCount++;
      }
    }

    // Sort by score desc
    const ranked = Array.from(userMap.values())
      .sort((a, b) => b.score - a.score)
      .map((entry, idx) => ({
        rank: idx + 1,
        userId: entry.userId,
        name: entry.name,
        email: entry.email,
        image: entry.image,
        totalSolved: entry.solvedProblems.size,
        score: entry.score,
        easyCount: entry.easyCount,
        mediumCount: entry.mediumCount,
        hardCount: entry.hardCount,
      }));

    // Attach current user's rank
    const session = await auth();
    const currentUserId = session?.user?.id;
    const currentUserRank = currentUserId
      ? ranked.find((r) => r.userId === currentUserId)?.rank ?? null
      : null;

    return NextResponse.json({
      leaderboard: ranked.slice(0, 100), // top 100
      currentUserRank,
      currentUserId,
    });
  } catch (error) {
    console.error("Leaderboard error:", error);
    return NextResponse.json({ error: "Failed to fetch leaderboard" }, { status: 500 });
  }
}
