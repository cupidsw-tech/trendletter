import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { getSessionUser } from "@/lib/session";

export async function GET(req: NextRequest) {
  const user = await getSessionUser();
  if (!user) return NextResponse.json([], { status: 401 });

  const { searchParams } = new URL(req.url);
  const today = searchParams.get("today");
  const page = Number(searchParams.get("page") || "1");
  const limit = Number(searchParams.get("limit") || "20");

  const where: any = {
    source: { userId: user.id },
  };

  if (today === "true") {
    const startOfDay = new Date();
    startOfDay.setHours(0, 0, 0, 0);
    where.crawledAt = { gte: startOfDay };
  }

  const articles = await prisma.article.findMany({
    where,
    include: {
      source: { select: { name: true, category: true } },
    },
    orderBy: { crawledAt: "desc" },
    skip: (page - 1) * limit,
    take: limit,
  });

  return NextResponse.json(articles);
}
