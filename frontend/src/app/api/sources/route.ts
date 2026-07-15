import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { getSessionUser } from "@/lib/session";
import { FALLBACK_SOURCES } from "@/lib/fallback-sources";

export async function GET() {
  const user = await getSessionUser();
  if (!user) return NextResponse.json([], { status: 401 });

  try {
    const sources = await prisma.source.findMany({
      where: { userId: user.id },
      orderBy: { createdAt: "desc" },
    });
    // DB에 소스가 없거나(시드 전) 정상 조회 시 DB 값 반환
    return NextResponse.json(sources);
  } catch {
    // Neon 다운 등 DB 장애 → 실제 발송 소스(urls.json 스냅샷)로 폴백
    return NextResponse.json(FALLBACK_SOURCES, {
      headers: { "x-source": "fallback-urls-json" },
    });
  }
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
