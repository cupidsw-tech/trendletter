import { redirect } from "next/navigation";
import { getSessionUser } from "@/lib/session";
import { isAdminEmail } from "@/lib/admin";
import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

export default async function AdminPage() {
  const user = await getSessionUser();
  if (!user) redirect("/login");
  if (!isAdminEmail(user.email)) redirect("/dashboard");

  const users = await prisma.user.findMany({
    orderBy: { createdAt: "desc" },
    include: { _count: { select: { sources: true } } },
  });

  const totalSources = users.reduce((s, u) => s + u._count.sources, 0);
  const tgCount = users.filter((u) => u.deliverTelegram).length;

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-1">🛠️ 관리자 · 회원 관리</h1>
      <p className="text-gray-500 mb-6">전체 회원과 구독 현황을 한눈에 봅니다.</p>

      <div className="grid grid-cols-3 gap-3 mb-6">
        <div className="bg-white rounded-xl border p-4">
          <div className="text-2xl font-bold">{users.length}</div>
          <div className="text-sm text-gray-500">전체 회원</div>
        </div>
        <div className="bg-white rounded-xl border p-4">
          <div className="text-2xl font-bold">{totalSources}</div>
          <div className="text-sm text-gray-500">총 구독 URL</div>
        </div>
        <div className="bg-white rounded-xl border p-4">
          <div className="text-2xl font-bold">{tgCount}</div>
          <div className="text-sm text-gray-500">텔레그램 사용</div>
        </div>
      </div>

      <div className="bg-white rounded-xl border overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-500">
            <tr>
              <th className="text-left px-4 py-3">이메일</th>
              <th className="text-left px-4 py-3">이름</th>
              <th className="text-left px-4 py-3">발송채널</th>
              <th className="text-left px-4 py-3">발송시각</th>
              <th className="text-left px-4 py-3">구독</th>
              <th className="text-left px-4 py-3">가입일</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => {
              const ch = [
                u.deliverWeb && "웹",
                u.deliverTelegram && "텔레그램",
                u.deliverKakao && "카카오",
              ]
                .filter(Boolean)
                .join(", ");
              return (
                <tr key={u.id} className="border-t">
                  <td className="px-4 py-3">{u.email}</td>
                  <td className="px-4 py-3">{u.name || "-"}</td>
                  <td className="px-4 py-3">{ch || "-"}</td>
                  <td className="px-4 py-3">
                    {String(u.scheduleHour).padStart(2, "0")}:
                    {String(u.scheduleMinute).padStart(2, "0")}
                  </td>
                  <td className="px-4 py-3">{u._count.sources}개</td>
                  <td className="px-4 py-3">
                    {new Date(u.createdAt).toLocaleDateString("ko-KR")}
                  </td>
                </tr>
              );
            })}
            {users.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-400">
                  아직 가입한 회원이 없습니다.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
