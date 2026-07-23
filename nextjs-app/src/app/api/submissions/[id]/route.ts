import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { auth } from "@/lib/auth";

type RouteContext = { params: Promise<{ id: string }> };

// GET /api/submissions/[id] — public-readable submission view
export async function GET(_req: Request, context: RouteContext) {
  try {
    const { id } = await context.params;
    const submissionId = parseInt(id);

    if (isNaN(submissionId)) {
      return NextResponse.json({ error: "Invalid ID" }, { status: 400 });
    }

    const submission = await prisma.submission.findUnique({
      where: { id: submissionId },
      include: {
        problem: { select: { name: true, shortCode: true, difficulty: true } },
        user: { select: { id: true, name: true, image: true } },
      },
    });

    if (!submission) {
      return NextResponse.json({ error: "Submission not found" }, { status: 404 });
    }

    // For non-AC submissions, only the owner or admin can see the code
    const session = await auth();
    const isOwner = session?.user?.id === submission.userId;
    const isAdmin = session?.user?.isAdmin;

    return NextResponse.json({
      id: submission.id,
      verdict: submission.verdict,
      language: submission.language,
      submitted: submission.submitted,
      // Only show code if it's the owner or an admin
      codeText: (isOwner || isAdmin) ? submission.codeText : null,
      canViewCode: isOwner || isAdmin,
      problem: submission.problem,
      user: {
        id: submission.user.id,
        name: submission.user.name,
        image: submission.user.image,
      },
    });
  } catch (error) {
    console.error("Submission GET error:", error);
    return NextResponse.json({ error: "Server error" }, { status: 500 });
  }
}
