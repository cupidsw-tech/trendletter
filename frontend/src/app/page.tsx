import { redirect } from "next/navigation";

// 로그인 제거: 방문 시 바로 대시보드로 이동.
export default function Home() {
  redirect("/dashboard");
}
