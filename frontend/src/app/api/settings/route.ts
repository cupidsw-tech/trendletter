import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { getSessionUser } from "@/lib/session";

export async function GET() {
  const user = await getSessionUser();
  if (!user) return NextResponse.json({}, { status: 401 });

  const u = await prisma.user.findUnique({
    where: { id: user.id },
    select: {
      deliverWeb: true,
      deliverTelegram: true,
      deliverKakao: true,
      telegramChatId: true,
      templateId: true,
      scheduleHour: true,
      scheduleMinute: true,
    },
  });

  return NextResponse.json(u);
}

export async function PUT(req: NextRequest) {
  const user = await getSessionUser();
  if (!user) return NextResponse.json({}, { status: 401 });

  const body = await req.json();

  await prisma.user.update({
    where: { id: user.id },
    data: {
      deliverWeb: body.deliverWeb,
      deliverTelegram: body.deliverTelegram,
      deliverKakao: body.deliverKakao,
      telegramChatId: body.telegramChatId || null,
      templateId: body.templateId || "compact",
      scheduleHour: body.scheduleHour,
      scheduleMinute: body.scheduleMinute,
    },
  });

  return NextResponse.json({ success: true });
}
