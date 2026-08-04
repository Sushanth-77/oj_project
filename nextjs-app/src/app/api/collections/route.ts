import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { auth } from "@/lib/auth";

// GET /api/collections — list all published collections
export async function GET() {
  try {
    const collections = await prisma.collection.findMany({
      where: { isPublished: true },
      orderBy: { createdAt: "desc" },
      include: {
        _count: { select: { problems: true } },
      },
    });

    return NextResponse.json(collections.map((c) => ({
      ...c,
      problemCount: c._count.problems,
      _count: undefined,
    })));
  } catch (error) {
    console.error("Collections GET error:", error);
    return NextResponse.json({ error: "Server error" }, { status: 500 });
  }
}

// POST /api/collections — admin creates collection
export async function POST(request: Request) {
  try {
    const session = await auth();
    if (!session?.user?.isAdmin) return NextResponse.json({ error: "Forbidden" }, { status: 403 });

    const { title, description, slug, isPublished, problemIds } = await request.json();
    if (!title || !slug) return NextResponse.json({ error: "title and slug required" }, { status: 400 });

    const collection = await prisma.collection.create({
      data: {
        title,
        description,
        slug,
        isPublished: isPublished ?? false,
        problems: problemIds?.length
          ? {
              create: problemIds.map((problemId: number, idx: number) => ({
                problemId,
                order: idx + 1,
              })),
            }
          : undefined,
      },
      include: { _count: { select: { problems: true } } },
    });

    return NextResponse.json(collection, { status: 201 });
  } catch (error: any) {
    if (error?.code === "P2002") return NextResponse.json({ error: "Slug already exists" }, { status: 400 });
    console.error("Collections POST error:", error);
    return NextResponse.json({ error: "Server error" }, { status: 500 });
  }
}
