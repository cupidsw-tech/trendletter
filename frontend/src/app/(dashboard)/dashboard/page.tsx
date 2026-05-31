"use client";

import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";

interface ArticleItem {
  id: string;
  title: string;
  url: string;
  summary: string | null;
  crawledAt: string;
  source: { name: string; category: string };
}

export default function DashboardPage() {
  const { data: session } = useSession();
  const [articles, setArticles] = useState<ArticleItem[]>([]);
  const [sourceCount, setSourceCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [crawling, setCrawling] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  async function fetchData() {
    setLoading(true);
    try {
      const [artRes, srcRes] = await Promise.all([
        fetch("/api/articles?today=true"),
        fetch("/api/sources"),
      ]);
      if (artRes.ok) setArticles(await artRes.json());
      if (srcRes.ok) {
        const sources = await srcRes.json();
        setSourceCount(sources.length);
      }
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  }

  async function handleCrawlNow() {
    setCrawling(true);
    try {
      await fetch("/api/crawl/trigger", { method: "POST" });
      // 잠시 후 새로고침
      setTimeout(fetchData, 3000);
    } catch (e) {
      console.error(e);
    }
    setCrawling(false);
  }

  const today = new Date().toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "long",
    day: "numeric",
    weekday: "long",
  });

  return (
    <div className="p-4 md:p-8 max-w-4xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold">오늘의 트렌드</h1>
          <p className="text-gray-500 text-sm">{today}</p>
        </div>
        <button
          onClick={handleCrawlNow}
          disabled={crawling}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
        >
          {crawling ? "수집 중..." : "지금 수집하기"}
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-white p-4 rounded-xl border">
          <p className="text-sm text-gray-500">감시 사이트</p>
          <p className="text-2xl font-bold">{sourceCount}개</p>
        </div>
        <div className="bg-white p-4 rounded-xl border">
          <p className="text-sm text-gray-500">오늘 수집된 글</p>
          <p className="text-2xl font-bold">{articles.length}건</p>
        </div>
      </div>

      {/* Articles */}
      {loading ? (
        <div className="text-center py-12 text-gray-400">불러오는 중...</div>
      ) : articles.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl border">
          <p className="text-gray-500 mb-2">오늘 수집된 아티클이 없습니다</p>
          <p className="text-sm text-gray-400">
            URL을 등록하고 &quot;지금 수집하기&quot;를 눌러보세요
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {articles.map((article) => (
            <div key={article.id} className="bg-white p-4 rounded-xl border">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xs px-2 py-0.5 bg-blue-50 text-blue-700 rounded-full font-medium">
                  {article.source.category}
                </span>
                <span className="text-xs text-gray-400">
                  {article.source.name}
                </span>
              </div>
              <h3 className="font-semibold mb-2">
                <a
                  href={article.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-blue-600"
                >
                  {article.title}
                </a>
              </h3>
              {article.summary && (
                <div className="text-sm text-gray-600 whitespace-pre-line leading-relaxed">
                  {article.summary.length > 300
                    ? article.summary.slice(0, 300) + "..."
                    : article.summary}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
