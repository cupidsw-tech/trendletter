"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/dashboard", label: "대시보드", icon: "📊" },
  { href: "/sources", label: "URL 관리", icon: "🔗" },
  { href: "/articles", label: "아티클", icon: "📄" },
  { href: "/resolutions", label: "나의 다짐", icon: "🌅" },
  { href: "/settings", label: "설정", icon: "⚙️" },
  { href: "/history", label: "발송 이력", icon: "📋" },
];

const ADMIN_ITEM = { href: "/admin", label: "관리자", icon: "🛠️" };

export function Sidebar() {
  const pathname = usePathname();
  // 로그인 제거(단일 소유자=관리자): 관리자 메뉴 항상 표시
  const NAV = [...NAV_ITEMS, ADMIN_ITEM];

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden md:flex w-56 bg-white border-r flex-col h-screen sticky top-0">
        <div className="p-4 border-b">
          <Link href="/dashboard" className="text-lg font-bold text-blue-700">
            TrendLetter
          </Link>
        </div>
        <nav className="flex-1 p-2 space-y-1">
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                pathname === item.href
                  ? "bg-blue-50 text-blue-700"
                  : "text-gray-600 hover:bg-gray-50"
              }`}
            >
              <span>{item.icon}</span>
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>

      {/* Mobile bottom nav */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t z-50 flex justify-around py-2 px-1 safe-bottom">
        {NAV.slice(0, 5).map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`flex flex-col items-center gap-0.5 px-2 py-1 text-xs ${
              pathname === item.href ? "text-blue-700" : "text-gray-500"
            }`}
          >
            <span className="text-lg">{item.icon}</span>
            {item.label}
          </Link>
        ))}
      </nav>
    </>
  );
}
