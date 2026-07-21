import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/db";

export async function GET(request: Request) {
  try {
    const session = await auth();
    if (!session?.user?.isAdmin) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const page = parseInt(searchParams.get("page") || "1");
    const limit = parseInt(searchParams.get("limit") || "20");
    const skip = (page - 1) * limit;

    const [submissions, total] = await Promise.all([
      prisma.submission.findMany({
        orderBy: { submitted: "desc" },
        take: limit,
        skip,
        include: {
          user: {
            select: { id: true, name: true, email: true, image: true },
          },
          problem: {
            select: { name: true, shortCode: true, difficulty: true },
          },
        },
      }),
      prisma.submission.count(),
    ]);

    return NextResponse.json({ submissions, total, page, limit });
  } catch (error) {
    console.error("Failed to fetch admin submissions:", error);
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}
