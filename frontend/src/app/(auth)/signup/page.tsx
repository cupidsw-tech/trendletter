import { redirect } from "next/navigation";

// 로그인 제거: 회원가입 없이 바로 대시보드로 이동.
export default function SignupPage() {
  redirect("/dashboard");
}
