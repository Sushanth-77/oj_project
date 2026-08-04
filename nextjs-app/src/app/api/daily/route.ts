import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { auth } from "@/lib/auth";

// GET /api/daily — returns today's daily challenge problem
export async function GET() {
  try {
    const session = await auth();
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    const daily = await prisma.problem.findFirst({
      where: {
        isDailyChallenge: true,
        dailyChallengeDate: {
          gte: today,
          lt: tomorrow,
        },
      },
      select: {
        id: true,
        name: true,
        shortCode: true,
        difficulty: true,
        topics: true,
      },
    });

    // If no specific date match, fall back to any active daily challenge
    if (!daily) {
      const fallback = await prisma.problem.findFirst({
        where: { isDailyChallenge: true },
        orderBy: { dailyChallengeDate: "desc" },
        select: {
          id: true,
          name: true,
          shortCode: true,
          difficulty: true,
          topics: true,
        },
      });
      return NextResponse.json({ daily: fallback });
    }

    return NextResponse.json({ daily });
  } catch (error) {
    console.error("Daily challenge GET error:", error);
    return NextResponse.json({ error: "Server error" }, { status: 500 });
  }
}

// POST /api/daily — admin sets daily challenge (requires isAdmin)
export async function POST(request: Request) {
  try {
    const session = await auth();
    if (!session?.user?.isAdmin) {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }

    const { problemId, date } = await request.json();
    if (!problemId) {
      return NextResponse.json({ error: "problemId required" }, { status: 400 });
    }

    // Clear previous daily challenge for the target date
    const targetDate = date ? new Date(date) : new Date();
    targetDate.setHours(0, 0, 0, 0);

    const nextDay = new Date(targetDate);
    nextDay.setDate(nextDay.getDate() + 1);

    await prisma.problem.updateMany({
      where: {
        isDailyChallenge: true,
        dailyChallengeDate: { gte: targetDate, lt: nextDay },
      },
      data: { isDailyChallenge: false, dailyChallengeDate: null },
    });

    // Set new daily challenge
    await prisma.problem.update({
      where: { id: problemId },
      data: { isDailyChallenge: true, dailyChallengeDate: targetDate },
    });

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Daily challenge POST error:", error);
    return NextResponse.json({ error: "Server error" }, { status: 500 });
  }
}
