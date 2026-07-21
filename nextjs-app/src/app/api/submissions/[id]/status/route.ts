import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/db";

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { id } = await params;
    const submissionId = parseInt(id);

    const submission = await prisma.submission.findUnique({
      where: { id: submissionId },
      select: {
        id: true,
        verdict: true,
        userId: true,
      },
    });

    if (!submission) {
      return NextResponse.json({ error: "Submission not found" }, { status: 404 });
    }

    // Ensure users can only see their own submission status (or admin)
    if (submission.userId !== session.user.id && !session.user.isAdmin) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 403 });
    }

    return NextResponse.json({
      id: submission.id,
      status: submission.verdict, // Maps to Django's 'status' field in AJAX response
    });
  } catch (error) {
    console.error("Failed to fetch submission status:", error);
    return NextResponse.json(
      { error: "Failed to fetch submission status" },
      { status: 500 }
    );
  }
}
