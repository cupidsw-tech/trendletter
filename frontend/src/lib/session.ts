import { prisma } from "./prisma";

// 로그인 제거(단일 소유자 사용): 세션 없이 항상 소유자 계정으로 자동 인증.
// 소유자 이메일 우선, 없으면 가장 먼저 생성된 계정으로 폴백.
const OWNER_EMAIL = "jsw@bydream.co.kr";
// DB(Neon) 다운 시에도 인증 단계가 500 나지 않도록 하는 소유자 고정값.
const OWNER_FALLBACK = { id: "c23a23b68e59c4c8c93728ee1", email: OWNER_EMAIL };

export async function getSessionUser() {
  try {
    const user =
      (await prisma.user.findUnique({ where: { email: OWNER_EMAIL } })) ??
      (await prisma.user.findFirst({ orderBy: { createdAt: "asc" } }));
    if (user) return { id: user.id, email: user.email };
  } catch {
    // Neon 컴퓨트 쿼터 초과 등 DB 장애 → 고정 소유자로 폴백(데이터 조회는 각 라우트에서 처리)
  }
  return OWNER_FALLBACK;
}
