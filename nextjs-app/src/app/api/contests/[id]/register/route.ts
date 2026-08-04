import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/db";

type RouteContext = { params: Promise<{ id: string }> };

// POST /api/contests/[id]/register — register or unregister for a contest
export async function POST(_req: Request, context: RouteContext) {
  try {
    const session = await auth();
    if (!session?.user?.id) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

    const { id } = await context.params;
    const contestId = parseInt(id);
    if (isNaN(contestId)) return NextResponse.json({ error: "Invalid ID" }, { status: 400 });

    const contest = await prisma.contest.findUnique({
      where: { id: contestId },
      select: { id: true, startsAt: true, endsAt: true, isPublished: true },
    });
    if (!contest || !contest.isPublished) {
      return NextResponse.json({ error: "Contest not found" }, { status: 404 });
    }

    // Can't register after contest ends
    if (new Date() > contest.endsAt) {
      return NextResponse.json({ error: "Contest has ended" }, { status: 400 });
    }

    const existing = await prisma.contestRegistration.findUnique({
      where: { contestId_userId: { contestId, userId: session.user.id } },
    });

    if (existing) {
      // Unregister
      await prisma.contestRegistration.delete({ where: { id: existing.id } });
      return NextResponse.json({ registered: false });
    } else {
      // Register
      await prisma.contestRegistration.create({
        data: { contestId, userId: session.user.id },
      });
      return NextResponse.json({ registered: true });
    }
  } catch (error) {
    console.error("Contest register POST error:", error);
    return NextResponse.json({ error: "Server error" }, { status: 500 });
  }
}
