import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/db";
import { submissionSchema } from "@/lib/validations";
import { executeCode } from "@/lib/piston";
import { evaluateExecution } from "@/lib/judge";
import { Verdict } from "@/types";
import { processAcSubmission, seedBadges } from "@/lib/badges";

export async function GET(request: Request) {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const limit = parseInt(searchParams.get("limit") || "10");
    const problemId = searchParams.get("problemId");

    let whereClause: any = { userId: session.user.id };
    if (problemId) {
      whereClause.problemId = parseInt(problemId);
    }

    const submissions = await prisma.submission.findMany({
      where: whereClause,
      orderBy: { submitted: "desc" },
      take: limit,
      include: {
        problem: {
          select: { name: true, shortCode: true, difficulty: true },
        },
      },
    });

    return NextResponse.json(submissions);
  } catch (error) {
    console.error("Failed to fetch submissions:", error);
    return NextResponse.json(
      { error: "Failed to fetch submissions" },
      { status: 500 }
    );
  }
}

export async function POST(request: Request) {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const json = await request.json();
    const result = submissionSchema.safeParse(json);

    if (!result.success) {
      return NextResponse.json(
        { error: "Invalid input", details: result.error.format() },
        { status: 400 }
      );
    }

    const { problemId, codeText, language } = result.data;

    // Create the submission initially with PE (Pending Evaluation)
    const submission = await prisma.submission.create({
      data: {
        problemId,
        userId: session.user.id,
        codeText,
        language,
        verdict: "PE",
      },
    });

    // Fetch test cases
    const testCases = await prisma.testCase.findMany({
      where: { problemId },
      orderBy: { order: "asc" },
    });

    if (testCases.length === 0) {
      // If no test cases, just accept it (for now, or maybe CE)
      await prisma.submission.update({
        where: { id: submission.id },
        data: { verdict: "AC" },
      });
      return NextResponse.json({ id: submission.id, verdict: "AC" });
    }

    // Execute in the background (we'll await it here for simplicity since Piston is fast,
    // but in a real Vercel app we'd ideally trigger an async job or Edge function.
    // For this migration, we await it within the Next.js API route limit of 15s).
    
    let finalVerdict: Verdict = "AC";
    let finalErrorDetail: string | null = null;

    try {
      for (const testCase of testCases) {
        const runResult = await executeCode(language, codeText, testCase.input);
        const evalResult = evaluateExecution(runResult, testCase.output);

        if (evalResult.verdict !== "AC") {
          finalVerdict = evalResult.verdict;
          finalErrorDetail = evalResult.details?.error || null;
          break; // Stop on first failure
        }
      }
    } catch (execError) {
      console.error("Execution pipeline error:", execError);
      finalVerdict = "IE";
    }

    // Update submission with final verdict
    const updatedSubmission = await prisma.submission.update({
      where: { id: submission.id },
      data: { verdict: finalVerdict },
    });

    // Award badges & update streak on AC
    let newlyAwardedBadges: string[] = [];
    if (finalVerdict === "AC") {
      try {
        await seedBadges(); // Ensure badge definitions exist (idempotent)
        newlyAwardedBadges = await processAcSubmission(session.user.id!);
      } catch (badgeError) {
        console.error("Badge processing error (non-fatal):", badgeError);
      }
    }

    return NextResponse.json({ 
      id: updatedSubmission.id, 
      verdict: updatedSubmission.verdict,
      errorDetail: finalErrorDetail,
      newBadges: newlyAwardedBadges,
    });

  } catch (error) {
    console.error("Failed to submit code:", error);
    return NextResponse.json(
      { error: "Internal Error" },
      { status: 500 }
    );
  }
}
