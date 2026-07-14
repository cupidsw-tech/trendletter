import { Sidebar } from "@/components/sidebar";

// 로그인 제거: 세션 검사 없이 바로 대시보드 접근 허용.
export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 pb-20 md:pb-0">{children}</main>
    </div>
  );
}
