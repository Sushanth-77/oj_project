import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { auth } from "@/lib/auth";

type RouteContext = { params: Promise<{ shortCode: string }> };

// GET /api/problems/[shortCode]/notes — fetch user's note for this problem
export async function GET(_req: Request, context: RouteContext) {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      return NextResponse.json({ content: "" });
    }
    const { shortCode } = await context.params;
    const problem = await prisma.problem.findUnique({ where: { shortCode }, select: { id: true } });
    if (!problem) return NextResponse.json({ content: "" });

    const note = await prisma.problemNote.findUnique({
      where: { userId_problemId: { userId: session.user.id, problemId: problem.id } },
      select: { content: true, updatedAt: true },
    });
    return NextResponse.json({ content: note?.content ?? "", updatedAt: note?.updatedAt ?? null });
  } catch (error) {
    console.error("Notes GET error:", error);
    return NextResponse.json({ error: "Server error" }, { status: 500 });
  }
}

// POST /api/problems/[shortCode]/notes — save/update note
export async function POST(req: Request, context: RouteContext) {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }
    const { shortCode } = await context.params;
    const problem = await prisma.problem.findUnique({ where: { shortCode }, select: { id: true } });
    if (!problem) return NextResponse.json({ error: "Not found" }, { status: 404 });

    const { content } = await req.json();
    if (typeof content !== "string") {
      return NextResponse.json({ error: "Invalid content" }, { status: 400 });
    }

    const note = await prisma.problemNote.upsert({
      where: { userId_problemId: { userId: session.user.id, problemId: problem.id } },
      update: { content },
      create: { userId: session.user.id, problemId: problem.id, content },
    });
    return NextResponse.json({ content: note.content, updatedAt: note.updatedAt });
  } catch (error) {
    console.error("Notes POST error:", error);
    return NextResponse.json({ error: "Server error" }, { status: 500 });
  }
}
