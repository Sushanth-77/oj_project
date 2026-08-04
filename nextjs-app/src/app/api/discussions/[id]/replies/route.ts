import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/db";

type RouteContext = { params: Promise<{ id: string }> };

// POST /api/discussions/[id]/replies — add a reply to a discussion
export async function POST(request: Request, context: RouteContext) {
  try {
    const session = await auth();
    if (!session?.user?.id) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

    const { id } = await context.params;
    const discussionId = parseInt(id);
    if (isNaN(discussionId)) return NextResponse.json({ error: "Invalid ID" }, { status: 400 });

    const { body } = await request.json();
    if (!body || body.trim().length < 5) {
      return NextResponse.json({ error: "Reply must be at least 5 characters" }, { status: 400 });
    }

    const discussion = await prisma.discussion.findUnique({
      where: { id: discussionId },
      include: { user: { select: { id: true } } },
    });
    if (!discussion) return NextResponse.json({ error: "Discussion not found" }, { status: 404 });

    const reply = await prisma.discussionReply.create({
      data: {
        discussionId,
        userId: session.user.id,
        body: body.trim(),
      },
      include: {
        user: { select: { id: true, name: true, image: true } },
      },
    });

    // Notify discussion author if someone else replies
    if (discussion.userId !== session.user.id) {
      const replier = await prisma.user.findUnique({ where: { id: session.user.id }, select: { name: true } });
      await prisma.notification.create({
        data: {
          userId: discussion.userId,
          type: "reply",
          title: "💬 New Reply",
          message: `${replier?.name || "Someone"} replied to your discussion: "${discussion.title}"`,
          link: `/problems/discussion/${discussionId}`,
        },
      });
    }

    return NextResponse.json(reply, { status: 201 });
  } catch (error) {
    console.error("Discussion reply POST error:", error);
    return NextResponse.json({ error: "Server error" }, { status: 500 });
  }
}
