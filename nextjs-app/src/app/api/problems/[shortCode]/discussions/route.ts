import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/db";
import { z } from "zod";

const discussionSchema = z.object({
  title: z.string().min(3, "Title must be at least 3 characters").max(200),
  body: z.string().min(10, "Body must be at least 10 characters").max(10000),
});

type RouteContext = { params: Promise<{ shortCode: string }> };

// GET /api/problems/[shortCode]/discussions — list discussions for a problem
export async function GET(request: Request, context: RouteContext) {
  try {
    const { shortCode } = await context.params;
    const { searchParams } = new URL(request.url);
    const page = parseInt(searchParams.get("page") || "1");
    const limit = 15;

    const problem = await prisma.problem.findUnique({
      where: { shortCode },
      select: { id: true },
    });
    if (!problem) return NextResponse.json({ error: "Problem not found" }, { status: 404 });

    const [discussions, total] = await Promise.all([
      prisma.discussion.findMany({
        where: { problemId: problem.id },
        orderBy: [{ isPinned: "desc" }, { createdAt: "desc" }],
        skip: (page - 1) * limit,
        take: limit,
        include: {
          user: { select: { id: true, name: true, image: true } },
          _count: { select: { replies: true, votes: true } },
          votes: true,
        },
      }),
      prisma.discussion.count({ where: { problemId: problem.id } }),
    ]);

    return NextResponse.json({
      discussions: discussions.map((d) => ({
        ...d,
        replyCount: d._count.replies,
        voteScore: d.votes.reduce((sum, v) => sum + v.value, 0),
        votes: undefined,
        _count: undefined,
      })),
      total,
      pages: Math.ceil(total / limit),
    });
  } catch (error) {
    console.error("Discussions GET error:", error);
    return NextResponse.json({ error: "Server error" }, { status: 500 });
  }
}

// POST /api/problems/[shortCode]/discussions — create new discussion
export async function POST(request: Request, context: RouteContext) {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { shortCode } = await context.params;
    const json = await request.json();
    const parsed = discussionSchema.safeParse(json);
    if (!parsed.success) {
      return NextResponse.json({ error: "Invalid input" }, { status: 400 });
    }

    const problem = await prisma.problem.findUnique({
      where: { shortCode },
      select: { id: true },
    });
    if (!problem) return NextResponse.json({ error: "Problem not found" }, { status: 404 });

    const discussion = await prisma.discussion.create({
      data: {
        problemId: problem.id,
        userId: session.user.id,
        title: parsed.data.title,
        body: parsed.data.body,
      },
      include: {
        user: { select: { id: true, name: true, image: true } },
      },
    });

    return NextResponse.json(discussion, { status: 201 });
  } catch (error) {
    console.error("Discussions POST error:", error);
    return NextResponse.json({ error: "Server error" }, { status: 500 });
  }
}
