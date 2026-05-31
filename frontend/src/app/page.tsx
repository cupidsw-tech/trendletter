import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-slate-900 to-slate-800 text-white px-4">
      <div className="max-w-2xl text-center">
        <h1 className="text-5xl font-bold mb-4">📰 트렌드레터</h1>
        <p className="text-lg text-slate-300 mb-2">
          관심 있는 사이트의 최신 트렌드를 매일 아침 자동으로 요약해
        </p>
        <p className="text-lg text-slate-300 mb-10">
          텔레그램 · 카카오톡 · 웹으로 받아보세요.
        </p>
        <div className="flex gap-4 justify-center">
          <Link
            href="/signup"
            className="bg-blue-600 hover:bg-blue-700 px-8 py-3 rounded-xl font-semibold"
          >
            시작하기
          </Link>
          <Link
            href="/login"
            className="bg-white/10 hover:bg-white/20 px-8 py-3 rounded-xl font-semibold"
          >
            로그인
          </Link>
        </div>
      </div>
    </div>
  );
}
