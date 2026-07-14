import { redirect } from "next/navigation";

// 로그인 제거: /login 방문 시에도 바로 대시보드로 이동(아이디/비번 입력 없음).
export default function LoginPage() {
  redirect("/dashboard");
}
