// 관리자 이메일 화이트리스트 (별도 마이그레이션 없이 권한 처리)
// 필요 시 ADMIN_EMAILS 환경변수(콤마구분)로 덮어쓸 수 있음.
const DEFAULT_ADMINS = [
  "jsw@bydream.co.kr",
  "datalab@bydream.co.kr",
  "promise4123@navercom",
  "promise4123@naver.com",
  "admin@trendletter.kr",
];

export function getAdminEmails(): string[] {
  const env = process.env.ADMIN_EMAILS;
  if (env) return env.split(",").map((s) => s.trim().toLowerCase()).filter(Boolean);
  return DEFAULT_ADMINS.map((s) => s.toLowerCase());
}

export function isAdminEmail(email?: string | null): boolean {
  if (!email) return false;
  return getAdminEmails().includes(email.toLowerCase());
}
