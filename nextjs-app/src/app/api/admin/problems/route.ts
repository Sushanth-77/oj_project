import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/db";
import { createProblemSchema } from "@/lib/validations";
import { getTopicTags } from "@/lib/groq";

export async function GET(request: Request) {
  try {
    const session = await auth();
    if (!session?.user?.isAdmin) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const problems = await prisma.problem.findMany({
      orderBy: { createdAt: "desc" },
    });

    return NextResponse.json(problems);
  } catch (error) {
    console.error("Failed to fetch problems:", error);
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const session = await auth();
    if (!session?.user?.isAdmin) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const json = await request.json();
    const result = createProblemSchema.safeParse(json);

    if (!result.success) {
      return NextResponse.json(
        { error: "Invalid input", details: result.error.format() },
        { status: 400 }
      );
    }

    const existingProblem = await prisma.problem.findUnique({
      where: { shortCode: result.data.shortCode },
    });

    if (existingProblem) {
      return NextResponse.json(
        { error: "Problem with this short code already exists" },
        { status: 400 }
      );
    }

    // Auto-generate topic tags via Groq AI (non-blocking on failure)
    const topics = await getTopicTags(result.data.name, result.data.statement);

    // Extract optional templates from raw JSON (not in schema, so read from json directly)
    const templates = json.templates && typeof json.templates === "object" ? json.templates : undefined;

    const problem = await prisma.problem.create({
      data: {
        name: result.data.name,
        shortCode: result.data.shortCode,
        statement: result.data.statement,
        difficulty: result.data.difficulty,
        topics,
        templates,
        testCases: {
          create: result.data.testCases,
        },
      },
      include: {
        testCases: true,
      },
    });

    return NextResponse.json(problem, { status: 201 });
  } catch (error) {
    console.error("Failed to create problem:", error);
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}

export async function PUT(request: Request) {
    try {
      const session = await auth();
      if (!session?.user?.isAdmin) {
        return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
      }
  
      const { searchParams } = new URL(request.url);
      const id = searchParams.get("id");
      if (!id) {
          return NextResponse.json({ error: "Problem ID required" }, { status: 400 });
      }
  
      const json = await request.json();
      const result = createProblemSchema.safeParse(json);
  
      if (!result.success) {
        return NextResponse.json(
          { error: "Invalid input", details: result.error.format() },
          { status: 400 }
        );
      }
  
      const templates = json.templates && typeof json.templates === "object" ? json.templates : null;
      const editorial = json.editorial !== undefined ? json.editorial : undefined;
      const editorialCode = json.editorialCode !== undefined ? json.editorialCode : undefined;
      const isDailyChallenge = json.isDailyChallenge !== undefined ? !!json.isDailyChallenge : undefined;

      const problem = await prisma.problem.update({
        where: { id: parseInt(id) },
        data: {
          name: result.data.name,
          shortCode: result.data.shortCode,
          statement: result.data.statement,
          difficulty: result.data.difficulty,
          templates: templates ?? undefined,
          ...(editorial !== undefined && { editorial }),
          ...(editorialCode !== undefined && { editorialCode }),
          ...(isDailyChallenge !== undefined && { isDailyChallenge }),
          testCases: {
              deleteMany: {},
              create: result.data.testCases,
          }
        },
        include: {
          testCases: true,
        },
      });
  
      return NextResponse.json(problem);
    } catch (error) {
      console.error("Failed to update problem:", error);
      return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
    }
}

export async function DELETE(request: Request) {
    try {
        const session = await auth();
        if (!session?.user?.isAdmin) {
          return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
        }
    
        const { searchParams } = new URL(request.url);
        const id = searchParams.get("id");
        if (!id) {
            return NextResponse.json({ error: "Problem ID required" }, { status: 400 });
        }

        const problemId = parseInt(id);
    
        // Use a transaction: delete submissions first (no cascade in schema),
        // then test cases, then the problem itself.
        await prisma.$transaction([
          prisma.submission.deleteMany({ where: { problemId } }),
          prisma.testCase.deleteMany({ where: { problemId } }),
          prisma.problem.delete({ where: { id: problemId } }),
        ]);
    
        return new NextResponse(null, { status: 204 });
      } catch (error) {
        console.error("Failed to delete problem:", error);
        return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
      }
}
