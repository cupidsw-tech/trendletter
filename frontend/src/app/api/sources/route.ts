import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { getSessionUser } from "@/lib/session";

export async function GET() {
  const user = await getSessionUser();
  if (!user) return NextResponse.json([], { status: 401 });

  const sources = await prisma.source.findMany({
    where: { userId: user.id },
    orderBy: { createdAt: "desc" },
  });

  return NextResponse.json(sources);
}

export async function POST(req: NextRequest) {
  const user = await getSessionUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const { name, url, category } = await req.json();

  if (!name || !url) {
    return NextResponse.json({ error: "이름과 URL을 입력하세요" }, { status: 400 });
  }

  const source = await prisma.source.create({
    data: {
      userId: user.id,
      name,
      url,
      category: category || "기타",
    },
  });

  return NextResponse.json(source, { status: 201 });
}
