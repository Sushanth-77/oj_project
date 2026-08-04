import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/db";
import { z } from "zod";

type RouteContext = { params: Promise<{ id: string }> };

// GET /api/discussions/[id] — get single discussion with replies
export async function GET(_req: Request, context: RouteContext) {
  try {
    const { id } = await context.params;
    const discussionId = parseInt(id);
    if (isNaN(discussionId)) return NextResponse.json({ error: "Invalid ID" }, { status: 400 });

    const discussion = await prisma.discussion.findUnique({
      where: { id: discussionId },
      include: {
        user: { select: { id: true, name: true, image: true } },
        replies: {
          include: { user: { select: { id: true, name: true, image: true } } },
          orderBy: { createdAt: "asc" },
        },
        votes: true,
      },
    });

    if (!discussion) return NextResponse.json({ error: "Not found" }, { status: 404 });

    return NextResponse.json({
      ...discussion,
      voteScore: discussion.votes.reduce((sum, v) => sum + v.value, 0),
    });
  } catch (error) {
    console.error("Discussion GET error:", error);
    return NextResponse.json({ error: "Server error" }, { status: 500 });
  }
}

// DELETE /api/discussions/[id] — delete own discussion
export async function DELETE(_req: Request, context: RouteContext) {
  try {
    const session = await auth();
    if (!session?.user?.id) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

    const { id } = await context.params;
    const discussionId = parseInt(id);
    if (isNaN(discussionId)) return NextResponse.json({ error: "Invalid ID" }, { status: 400 });

    const discussion = await prisma.discussion.findUnique({ where: { id: discussionId } });
    if (!discussion) return NextResponse.json({ error: "Not found" }, { status: 404 });

    const canDelete = discussion.userId === session.user.id || session.user.isAdmin;
    if (!canDelete) return NextResponse.json({ error: "Forbidden" }, { status: 403 });

    await prisma.discussion.delete({ where: { id: discussionId } });
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Discussion DELETE error:", error);
    return NextResponse.json({ error: "Server error" }, { status: 500 });
  }
}
