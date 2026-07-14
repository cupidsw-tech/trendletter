import { prisma } from "./prisma";

// 로그인 제거(단일 소유자 사용): 세션 없이 항상 소유자 계정으로 자동 인증.
// 소유자 이메일 우선, 없으면 가장 먼저 생성된 계정으로 폴백.
const OWNER_EMAIL = "jsw@bydream.co.kr";

export async function getSessionUser() {
  const user =
    (await prisma.user.findUnique({ where: { email: OWNER_EMAIL } })) ??
    (await prisma.user.findFirst({ orderBy: { createdAt: "asc" } }));
  if (!user) return null;
  return { id: user.id, email: user.email };
}
