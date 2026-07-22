import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/db";

export async function GET() {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      // Not logged in — return empty set (no error)
      return NextResponse.json({ solvedProblemIds: [] });
    }

    // Find distinct problem IDs where this user has at least one AC submission
    const acSubmissions = await prisma.submission.findMany({
      where: {
        userId: session.user.id,
        verdict: "AC",
      },
      select: { problemId: true },
      distinct: ["problemId"],
    });

    const solvedProblemIds = acSubmissions.map((s) => s.problemId);
    return NextResponse.json({ solvedProblemIds });
  } catch (error) {
    console.error("Failed to fetch solved problems:", error);
    return NextResponse.json(
      { error: "Failed to fetch solved problems" },
      { status: 500 }
    );
  }
}
