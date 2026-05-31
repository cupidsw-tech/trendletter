import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { getSessionUser } from "@/lib/session";

const KAKAO_CLIENT_ID = process.env.KAKAO_CLIENT_ID || "";
const KAKAO_REDIRECT_URI =
  (process.env.NEXTAUTH_URL || "http://localhost:3000") +
  "/api/auth/kakao/callback";

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const code = searchParams.get("code");

  if (!code) {
    return NextResponse.redirect(new URL("/settings?kakao=error", req.url));
  }

  // 1) 인가 코드로 토큰 발급
  const tokenRes = await fetch("https://kauth.kakao.com/oauth/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "authorization_code",
      client_id: KAKAO_CLIENT_ID,
      redirect_uri: KAKAO_REDIRECT_URI,
      code,
    }),
  });

  if (!tokenRes.ok) {
    return NextResponse.redirect(new URL("/settings?kakao=error", req.url));
  }

  const tokenData = await tokenRes.json();
  const { access_token, refresh_token } = tokenData;

  // 2) 로그인된 사용자에게 토큰 저장
  const user = await getSessionUser();
  if (!user) {
    return NextResponse.redirect(new URL("/login", req.url));
  }

  await prisma.user.update({
    where: { id: user.id },
    data: {
      kakaoAccessToken: access_token,
      kakaoRefreshToken: refresh_token || null,
      deliverKakao: true,
    },
  });

  return NextResponse.redirect(new URL("/settings?kakao=success", req.url));
}
