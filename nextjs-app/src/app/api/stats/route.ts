import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";

// GET /api/stats — public platform-wide stats for the landing page
export async function GET() {
  try {
    const [totalProblems, totalSubmissions, totalUsers, totalAC] = await Promise.all([
      prisma.problem.count(),
      prisma.submission.count(),
      prisma.user.count(),
      prisma.submission.count({ where: { verdict: "AC" } }),
    ]);

    const acceptanceRate = totalSubmissions > 0
      ? Math.round((totalAC / totalSubmissions) * 100)
      : 0;

    return NextResponse.json({
      totalProblems,
      totalSubmissions,
      totalUsers,
      totalAC,
      acceptanceRate,
    });
  } catch (error) {
    console.error("Stats error:", error);
    return NextResponse.json({ error: "Failed to fetch stats" }, { status: 500 });
  }
}
