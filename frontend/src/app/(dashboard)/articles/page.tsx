"use client";

import { useEffect, useMemo, useState } from "react";

interface ArticleItem {
  id: string;
  title: string;
  url: string;
  summary: string | null;
  crawledAt: string;
  pdfUrls: string[];
  source: { name: string; category: string };
}

function batchKey(s: string) {
  const d = new Date(s);
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}.${p(d.getMonth() + 1)}.${p(d.getDate())}`;
}

export default function ArticlesPage() {
  const [articles, setArticles] = useState<ArticleItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [selectedDate, setSelectedDate] = useState<string>("");

  useEffect(() => {
    fetchArticles();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  async function fetchArticles() {
    setLoading(true);
    const res = await fetch(`/api/articles?page=${page}&limit=100`);
    if (res.ok) setArticles(await res.json());
    setLoading(false);
  }

  // 날짜별 그룹 (최신순)
  const groups = useMemo(() => {
    const g: { date: string; items: ArticleItem[] }[] = [];
    for (const a of articles) {
      const k = batchKey(a.crawledAt);
      let x = g.find((y) => y.date === k);
      if (!x) {
        x = { date: k, items: [] };
        g.push(x);
      }
      x.items.push(a);
    }
    return g;
  }, [articles]);

  const dates = groups.map((g) => g.date);
  // 선택된 날짜(없으면 최신) 기준으로 보여줄 그룹
  const activeDate = selectedDate || dates[0] || "";
  const activeGroup = groups.find((g) => g.date === activeDate);

  return (
    <div className="p-4 md:p-8 max-w-3xl">
      <div className="flex items-center justify-between mb-6 gap-3">
        <h1 className="text-2xl font-bold">아티클</h1>
        {/* 우측 상단 날짜 선택 */}
        {dates.length > 0 && (
          <select
            value={activeDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="text-sm border rounded-lg px-3 py-2 bg-white"
          >
            {dates.map((d) => {
              const cnt = groups.find((g) => g.date === d)?.items.length ?? 0;
              return (
                <option key={d} value={d}>
                  📅 {d} 09:00 ({cnt}건)
                </option>
              );
            })}
          </select>
        )}
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-400">불러오는 중...</div>
      ) : !activeGroup ? (
        <div className="text-center py-12 bg-white rounded-xl border">
          <p className="text-gray-500">아직 수집된 아티클이 없습니다</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border divide-y">
          <div className="px-5 py-3 bg-gray-50 text-sm font-semibold text-gray-600">
            {activeGroup.date} 09:00 · {activeGroup.items.length}건
          </div>
          {activeGroup.items.map((article) => {
            const pdfs = (article.pdfUrls || []).filter((u) =>
              u.startsWith("http")
            );
            return (
              <div key={article.id} className="px-5 py-4">
                <div className="flex items-center gap-2 mb-1.5">
                  <span className="text-[10px] bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded">
                    {article.source.category}
                  </span>
                  <span className="text-xs text-gray-400">
                    {article.source.name}
                  </span>
                </div>
                <h3 className="font-medium mb-1.5 leading-snug">
                  {article.title}
                </h3>
                {article.summary && (
                  <p className="text-sm text-gray-600 whitespace-pre-line leading-relaxed mb-2">
                    {article.summary}
                  </p>
                )}
                <div className="flex flex-wrap items-center gap-2">
                  <a
                    href={article.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs bg-blue-600 text-white px-3 py-1.5 rounded-lg"
                  >
                    원문 보기 →
                  </a>
                  {pdfs.map((u, i) => (
                    <a
                      key={i}
                      href={u}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs bg-gray-200 text-gray-700 px-3 py-1.5 rounded-lg"
                    >
                      📎 PDF {pdfs.length > 1 ? i + 1 : ""}
                    </a>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {!loading && articles.length > 0 && (
        <div className="flex justify-center gap-2 mt-6">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-4 py-2 text-sm border rounded-lg disabled:opacity-40"
          >
            이전
          </button>
          <span className="px-3 py-2 text-sm text-gray-500">{page}</span>
          <button
            onClick={() => setPage((p) => p + 1)}
            disabled={articles.length < 100}
            className="px-4 py-2 text-sm border rounded-lg disabled:opacity-40"
          >
            다음
          </button>
        </div>
      )}
    </div>
  );
}
