import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/db";

type RouteContext = { params: Promise<{ shortCode: string }> };

// GET /api/problems/[shortCode]/editorial — returns editorial if unlocked
export async function GET(_req: Request, context: RouteContext) {
  try {
    const { shortCode } = await context.params;
    const session = await auth();

    const problem = await prisma.problem.findUnique({
      where: { shortCode },
      select: { id: true, editorial: true, editorialCode: true },
    });
    if (!problem) return NextResponse.json({ error: "Problem not found" }, { status: 404 });

    // Admins always have access
    if (session?.user?.isAdmin) {
      return NextResponse.json({
        unlocked: true,
        editorial: problem.editorial,
        editorialCode: problem.editorialCode,
      });
    }

    if (!session?.user?.id) {
      return NextResponse.json({ unlocked: false, reason: "Login to view editorials" });
    }

    // Check if user solved the problem
    const solvedCount = await prisma.submission.count({
      where: { userId: session.user.id, problemId: problem.id, verdict: "AC" },
    });

    if (solvedCount > 0) {
      return NextResponse.json({
        unlocked: true,
        editorial: problem.editorial,
        editorialCode: problem.editorialCode,
      });
    }

    // Check if user has 3+ attempts
    const attemptCount = await prisma.submission.count({
      where: { userId: session.user.id, problemId: problem.id },
    });

    if (attemptCount >= 3) {
      return NextResponse.json({
        unlocked: true,
        editorial: problem.editorial,
        editorialCode: problem.editorialCode,
      });
    }

    return NextResponse.json({
      unlocked: false,
      reason: `Solve the problem or make ${3 - attemptCount} more attempt(s) to unlock the editorial`,
      attemptsLeft: 3 - attemptCount,
    });
  } catch (error) {
    console.error("Editorial GET error:", error);
    return NextResponse.json({ error: "Server error" }, { status: 500 });
  }
}
