"use client";

import { useEffect, useState } from "react";

interface Source {
  id: string;
  name: string;
  url: string;
  category: string;
  isActive: boolean;
  lastCrawledAt: string | null;
}

const CATEGORIES = ["AI", "광고", "마케팅", "주식", "유통", "리워드", "HR", "기타"];

export default function SourcesPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [readOnly, setReadOnly] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [newName, setNewName] = useState("");
  const [newUrl, setNewUrl] = useState("");
  const [newCategory, setNewCategory] = useState("기타");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchSources();
  }, []);

  async function fetchSources() {
    setLoading(true);
    const res = await fetch("/api/sources");
    if (res.ok) {
      setReadOnly(res.headers.get("x-source") === "fallback-urls-json");
      setSources(await res.json());
    }
    setLoading(false);
  }

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    const res = await fetch("/api/sources", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: newName, url: newUrl, category: newCategory }),
    });
    if (res.ok) {
      setNewName("");
      setNewUrl("");
      setNewCategory("기타");
      setShowForm(false);
      fetchSources();
    }
    setSaving(false);
  }

  async function handleDelete(id: string) {
    if (!confirm("이 URL을 삭제하시겠습니까?")) return;
    await fetch(`/api/sources/${id}`, { method: "DELETE" });
    fetchSources();
  }

  async function handleToggle(id: string, isActive: boolean) {
    await fetch(`/api/sources/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ isActive: !isActive }),
    });
    fetchSources();
  }

  return (
    <div className="p-4 md:p-8 max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">URL 관리</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700"
        >
          {showForm ? "취소" : "+ URL 추가"}
        </button>
      </div>

      {readOnly && (
        <div className="mb-6 bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-amber-800">
          데이터베이스 점검 중입니다. 현재 목록은 <b>실제 매일 발송에 쓰이는 소스(18개)</b>이며,
          지금은 <b>읽기 전용</b>이라 추가·삭제가 저장되지 않습니다. (DB 복구 후 정상화)
        </div>
      )}

      {/* Add form */}
      {showForm && (
        <form
          onSubmit={handleAdd}
          className="bg-white p-4 rounded-xl border mb-6 space-y-3"
        >
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <input
              type="text"
              placeholder="사이트 이름"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              required
              className="px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <input
              type="url"
              placeholder="https://example.com/board"
              value={newUrl}
              onChange={(e) => setNewUrl(e.target.value)}
              required
              className="px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <select
              value={newCategory}
              onChange={(e) => setNewCategory(e.target.value)}
              className="px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
          <button
            type="submit"
            disabled={saving}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? "추가 중..." : "추가하기"}
          </button>
        </form>
      )}

      {/* Source list */}
      {loading ? (
        <div className="text-center py-12 text-gray-400">불러오는 중...</div>
      ) : sources.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl border">
          <p className="text-gray-500 mb-2">등록된 URL이 없습니다</p>
          <p className="text-sm text-gray-400">위의 &quot;+ URL 추가&quot; 버튼을 눌러 시작하세요</p>
        </div>
      ) : (
        <div className="space-y-2">
          {sources.map((source) => (
            <div
              key={source.id}
              className={`bg-white p-4 rounded-xl border flex flex-col sm:flex-row sm:items-center gap-3 ${
                !source.isActive ? "opacity-50" : ""
              }`}
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs px-2 py-0.5 bg-blue-50 text-blue-700 rounded-full font-medium">
                    {source.category}
                  </span>
                  <span className="font-medium text-sm truncate">
                    {source.name}
                  </span>
                </div>
                <p className="text-xs text-gray-400 truncate">{source.url}</p>
                {source.lastCrawledAt && (
                  <p className="text-xs text-gray-400 mt-1">
                    마지막 수집:{" "}
                    {new Date(source.lastCrawledAt).toLocaleString("ko-KR")}
                  </p>
                )}
              </div>
              <div className="flex gap-2 shrink-0">
                <button
                  onClick={() => handleToggle(source.id, source.isActive)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium ${
                    source.isActive
                      ? "bg-green-50 text-green-700"
                      : "bg-gray-100 text-gray-500"
                  }`}
                >
                  {source.isActive ? "활성" : "비활성"}
                </button>
                <button
                  onClick={() => handleDelete(source.id)}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium bg-red-50 text-red-600 hover:bg-red-100"
                >
                  삭제
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
