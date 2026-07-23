import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { auth } from "@/lib/auth";

type RouteContext = { params: Promise<{ shortCode: string }> };

// GET /api/problems/[shortCode]/bookmark — check if bookmarked
export async function GET(_req: Request, context: RouteContext) {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      return NextResponse.json({ bookmarked: false });
    }
    const { shortCode } = await context.params;
    const problem = await prisma.problem.findUnique({ where: { shortCode }, select: { id: true } });
    if (!problem) return NextResponse.json({ bookmarked: false });

    const bookmark = await prisma.bookmark.findUnique({
      where: { userId_problemId: { userId: session.user.id, problemId: problem.id } },
    });
    return NextResponse.json({ bookmarked: !!bookmark });
  } catch (error) {
    console.error("Bookmark GET error:", error);
    return NextResponse.json({ error: "Server error" }, { status: 500 });
  }
}

// POST /api/problems/[shortCode]/bookmark — toggle bookmark
export async function POST(_req: Request, context: RouteContext) {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }
    const { shortCode } = await context.params;
    const problem = await prisma.problem.findUnique({ where: { shortCode }, select: { id: true } });
    if (!problem) return NextResponse.json({ error: "Not found" }, { status: 404 });

    const existing = await prisma.bookmark.findUnique({
      where: { userId_problemId: { userId: session.user.id, problemId: problem.id } },
    });

    if (existing) {
      await prisma.bookmark.delete({ where: { id: existing.id } });
      return NextResponse.json({ bookmarked: false });
    } else {
      await prisma.bookmark.create({
        data: { userId: session.user.id, problemId: problem.id },
      });
      return NextResponse.json({ bookmarked: true });
    }
  } catch (error) {
    console.error("Bookmark POST error:", error);
    return NextResponse.json({ error: "Server error" }, { status: 500 });
  }
}
