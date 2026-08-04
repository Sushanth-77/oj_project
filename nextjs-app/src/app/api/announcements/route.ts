import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { auth } from "@/lib/auth";

// GET /api/announcements — get active announcements
export async function GET() {
  try {
    const announcements = await prisma.announcement.findMany({
      where: { isActive: true },
      orderBy: { createdAt: "desc" },
      take: 3,
    });
    return NextResponse.json(announcements);
  } catch (error) {
    console.error("Announcements GET error:", error);
    return NextResponse.json([]);
  }
}

// POST /api/announcements — admin creates announcement
export async function POST(request: Request) {
  try {
    const session = await auth();
    if (!session?.user?.isAdmin) return NextResponse.json({ error: "Forbidden" }, { status: 403 });

    const { message, link } = await request.json();
    if (!message) return NextResponse.json({ error: "message required" }, { status: 400 });

    const announcement = await prisma.announcement.create({
      data: { message, link },
    });
    return NextResponse.json(announcement, { status: 201 });
  } catch (error) {
    console.error("Announcements POST error:", error);
    return NextResponse.json({ error: "Server error" }, { status: 500 });
  }
}

// DELETE /api/announcements?id=X — admin deactivates announcement
export async function DELETE(request: Request) {
  try {
    const session = await auth();
    if (!session?.user?.isAdmin) return NextResponse.json({ error: "Forbidden" }, { status: 403 });

    const { searchParams } = new URL(request.url);
    const id = parseInt(searchParams.get("id") || "");
    if (isNaN(id)) return NextResponse.json({ error: "Invalid ID" }, { status: 400 });

    await prisma.announcement.update({ where: { id }, data: { isActive: false } });
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Announcements DELETE error:", error);
    return NextResponse.json({ error: "Server error" }, { status: 500 });
  }
}
