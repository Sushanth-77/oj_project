import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/db";

export async function GET(request: Request) {
  try {
    const session = await auth();
    if (!session?.user?.isAdmin) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const totalUsers = await prisma.user.count();
    const totalProblems = await prisma.problem.count();
    const totalSubmissions = await prisma.submission.count();
    
    // Submissions by verdict for charts
    const submissionsByVerdict = await prisma.submission.groupBy({
        by: ['verdict'],
        _count: {
            _all: true,
        },
    });

    const recentSubmissions = await prisma.submission.findMany({
        take: 5,
        orderBy: { submitted: "desc" },
        include: {
            user: { select: { name: true, email: true } },
            problem: { select: { name: true, shortCode: true } }
        }
    });

    return NextResponse.json({
        totalUsers,
        totalProblems,
        totalSubmissions,
        submissionsByVerdict,
        recentSubmissions
    });
  } catch (error) {
    console.error("Failed to fetch analytics:", error);
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}
