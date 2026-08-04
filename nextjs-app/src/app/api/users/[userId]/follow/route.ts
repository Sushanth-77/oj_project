import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/db";

type RouteContext = { params: Promise<{ userId: string }> };

// POST /api/users/[userId]/follow — follow or unfollow a user
export async function POST(_req: Request, context: RouteContext) {
  try {
    const session = await auth();
    if (!session?.user?.id) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

    const { userId } = await context.params;
    if (userId === session.user.id) {
      return NextResponse.json({ error: "Cannot follow yourself" }, { status: 400 });
    }

    const target = await prisma.user.findUnique({ where: { id: userId }, select: { id: true, name: true } });
    if (!target) return NextResponse.json({ error: "User not found" }, { status: 404 });

    const existing = await prisma.follow.findUnique({
      where: { followerId_followingId: { followerId: session.user.id, followingId: userId } },
    });

    if (existing) {
      // Unfollow
      await prisma.follow.delete({ where: { id: existing.id } });
      return NextResponse.json({ following: false });
    } else {
      // Follow
      await prisma.follow.create({
        data: { followerId: session.user.id, followingId: userId },
      });
      return NextResponse.json({ following: true });
    }
  } catch (error) {
    console.error("Follow POST error:", error);
    return NextResponse.json({ error: "Server error" }, { status: 500 });
  }
}

// GET /api/users/[userId]/follow — check if current user follows this user
export async function GET(_req: Request, context: RouteContext) {
  try {
    const session = await auth();
    if (!session?.user?.id) return NextResponse.json({ following: false });

    const { userId } = await context.params;
    const existing = await prisma.follow.findUnique({
      where: { followerId_followingId: { followerId: session.user.id, followingId: userId } },
    });

    // Also return counts
    const [followerCount, followingCount] = await Promise.all([
      prisma.follow.count({ where: { followingId: userId } }),
      prisma.follow.count({ where: { followerId: userId } }),
    ]);

    return NextResponse.json({ following: !!existing, followerCount, followingCount });
  } catch (error) {
    console.error("Follow GET error:", error);
    return NextResponse.json({ following: false });
  }
}
