import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const search = searchParams.get("search");

    let whereClause = {};
    if (search) {
      whereClause = {
        OR: [
          { name: { contains: search, mode: "insensitive" } },
          { statement: { contains: search, mode: "insensitive" } },
          { shortCode: { contains: search, mode: "insensitive" } },
        ],
      };
    }

    const problems = await prisma.problem.findMany({
      where: whereClause,
      orderBy: { id: "asc" },
      select: {
        id: true,
        name: true,
        shortCode: true,
        difficulty: true,
        statement: true,
      },
    });

    return NextResponse.json(problems);
  } catch (error) {
    console.error("Failed to fetch problems:", error);
    return NextResponse.json(
      { error: "Failed to fetch problems" },
      { status: 500 }
    );
  }
}
