import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/db";
import { getAIHint } from "@/lib/groq";

type RouteContext = { params: Promise<{ shortCode: string }> };

export async function POST(req: Request, context: RouteContext) {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { shortCode } = await context.params;
    const problem = await prisma.problem.findUnique({
      where: { shortCode },
      select: { statement: true },
    });

    if (!problem) {
      return NextResponse.json({ error: "Problem not found" }, { status: 404 });
    }

    const { currentCode = "", language = "python", hintLevel = 1 } = await req.json();

    if (![1, 2, 3].includes(hintLevel)) {
      return NextResponse.json({ error: "Invalid hint level (1-3)" }, { status: 400 });
    }

    const result = await getAIHint(
      problem.statement,
      currentCode,
      language,
      hintLevel as 1 | 2 | 3
    );

    if (!result.success) {
      return NextResponse.json({ error: result.error }, { status: 500 });
    }

    return NextResponse.json({ hint: result.hint, hintLevel });
  } catch (error) {
    console.error("Hint API error:", error);
    return NextResponse.json({ error: "Server error" }, { status: 500 });
  }
}
