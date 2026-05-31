import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { getSessionUser } from "@/lib/session";
import { triggerCrawl } from "@/lib/engine-client";

export async function POST() {
  const user = await getSessionUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const sources = await prisma.source.findMany({
    where: { userId: user.id, isActive: true },
  });

  if (sources.length === 0) {
    return NextResponse.json({ message: "등록된 URL이 없습니다" }, { status: 400 });
  }

  try {
    const result = await triggerCrawl(
      user.id,
      sources.map((s: { id: string; url: string; name: string; category: string }) => ({
        source_id: s.id,
        url: s.url,
        name: s.name,
        category: s.category,
      }))
    );
    return NextResponse.json(result);
  } catch (e: any) {
    return NextResponse.json(
      { error: "크롤링 엔진 호출 실패", detail: e.message },
      { status: 502 }
    );
  }
}
