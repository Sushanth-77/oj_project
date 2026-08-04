import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { auth } from "@/lib/auth";

// GET /api/contests — list contests (upcoming, live, past)
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const filter = searchParams.get("filter") || "all"; // upcoming, live, past, all

    const now = new Date();
    let where: any = { isPublished: true };

    if (filter === "upcoming") {
      where.startsAt = { gt: now };
    } else if (filter === "live") {
      where.startsAt = { lte: now };
      where.endsAt = { gte: now };
    } else if (filter === "past") {
      where.endsAt = { lt: now };
    }

    const contests = await prisma.contest.findMany({
      where,
      orderBy: { startsAt: "desc" },
      include: {
        _count: { select: { registrations: true, problems: true } },
      },
    });

    return NextResponse.json(contests.map((c) => ({
      ...c,
      registrationCount: c._count.registrations,
      problemCount: c._count.problems,
      status: now < c.startsAt ? "upcoming" : now <= c.endsAt ? "live" : "past",
      _count: undefined,
    })));
  } catch (error) {
    console.error("Contests GET error:", error);
    return NextResponse.json({ error: "Server error" }, { status: 500 });
  }
}

// POST /api/contests — admin creates contest
export async function POST(request: Request) {
  try {
    const session = await auth();
    if (!session?.user?.isAdmin) return NextResponse.json({ error: "Forbidden" }, { status: 403 });

    const { title, description, startsAt, endsAt, isPublished, problemIds } = await request.json();
    if (!title || !startsAt || !endsAt) {
      return NextResponse.json({ error: "title, startsAt, endsAt required" }, { status: 400 });
    }

    const contest = await prisma.contest.create({
      data: {
        title,
        description: description || "",
        startsAt: new Date(startsAt),
        endsAt: new Date(endsAt),
        isPublished: isPublished ?? false,
        problems: problemIds?.length
          ? {
              create: problemIds.map((problemId: number, idx: number) => ({
                problemId,
                order: idx + 1,
                points: 100,
              })),
            }
          : undefined,
      },
    });

    return NextResponse.json(contest, { status: 201 });
  } catch (error) {
    console.error("Contests POST error:", error);
    return NextResponse.json({ error: "Server error" }, { status: 500 });
  }
}
