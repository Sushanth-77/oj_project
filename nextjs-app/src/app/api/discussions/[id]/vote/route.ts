import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/db";

type RouteContext = { params: Promise<{ id: string }> };

// POST /api/discussions/[id]/vote — upvote (+1) or downvote (-1) a discussion
export async function POST(request: Request, context: RouteContext) {
  try {
    const session = await auth();
    if (!session?.user?.id) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

    const { id } = await context.params;
    const discussionId = parseInt(id);
    if (isNaN(discussionId)) return NextResponse.json({ error: "Invalid ID" }, { status: 400 });

    const { value } = await request.json();
    if (value !== 1 && value !== -1) {
      return NextResponse.json({ error: "Value must be 1 or -1" }, { status: 400 });
    }

    const discussion = await prisma.discussion.findUnique({ where: { id: discussionId } });
    if (!discussion) return NextResponse.json({ error: "Not found" }, { status: 404 });

    // Check existing vote
    const existing = await prisma.discussionVote.findUnique({
      where: { discussionId_userId: { discussionId, userId: session.user.id } },
    });

    if (existing) {
      if (existing.value === value) {
        // Same vote — remove it (toggle off)
        await prisma.discussionVote.delete({
          where: { id: existing.id },
        });
      } else {
        // Different vote — update it
        await prisma.discussionVote.update({
          where: { id: existing.id },
          data: { value },
        });
      }
    } else {
      // New vote
      await prisma.discussionVote.create({
        data: { discussionId, userId: session.user.id, value },
      });
    }

    // Return updated vote score
    const votes = await prisma.discussionVote.findMany({ where: { discussionId } });
    const voteScore = votes.reduce((sum, v) => sum + v.value, 0);

    return NextResponse.json({ voteScore });
  } catch (error) {
    console.error("Vote POST error:", error);
    return NextResponse.json({ error: "Server error" }, { status: 500 });
  }
}
