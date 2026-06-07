import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { getSessionUser } from "@/lib/session";

export async function GET() {
  const user = await getSessionUser();
  if (!user) return NextResponse.json({}, { status: 401 });

  const u = await prisma.user.findUnique({
    where: { id: user.id },
    select: { resolutions: true },
  });

  return NextResponse.json({ resolutions: u?.resolutions ?? "" });
}

export async function PUT(req: NextRequest) {
  const user = await getSessionUser();
  if (!user) return NextResponse.json({}, { status: 401 });

  const body = await req.json();
  const resolutions =
    typeof body.resolutions === "string" && body.resolutions.trim()
      ? body.resolutions
      : null;

  await prisma.user.update({
    where: { id: user.id },
    data: { resolutions },
  });

  return NextResponse.json({ success: true });
}
