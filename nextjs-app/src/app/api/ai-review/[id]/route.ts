import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/db";
import { getAIReview } from "@/lib/groq";

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
      include: {
        problem: true,
      },
    });

    if (!submission) {
      return NextResponse.json({ error: "Submission not found" }, { status: 404 });
    }

    if (submission.userId !== session.user.id && !session.user.isAdmin) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 403 });
    }

    if (!submission.problem) {
       return NextResponse.json({ error: "Problem not found" }, { status: 404 });
    }

    const reviewResult = await getAIReview(
      submission.codeText,
      submission.language,
      submission.problem.statement
    );

    if (!reviewResult.success) {
      return NextResponse.json({ error: reviewResult.error }, { status: 500 });
    }

    return NextResponse.json({ success: true, review: reviewResult.review });
  } catch (error) {
    console.error("Failed to generate AI review:", error);
    return NextResponse.json(
      { error: "Failed to generate AI review" },
      { status: 500 }
    );
  }
}
