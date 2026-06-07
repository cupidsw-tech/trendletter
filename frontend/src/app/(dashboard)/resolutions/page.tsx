"use client";

import { useEffect, useState } from "react";

export default function ResolutionsPage() {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    fetch("/api/resolutions")
      .then((r) => r.json())
      .then((d) => {
        setText(d.resolutions || "");
        setLoading(false);
      });
  }, []);

  async function handleSave() {
    setSaving(true);
    setSaved(false);
    await fetch("/api/resolutions", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resolutions: text }),
    });
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  if (loading) {
    return (
      <div className="p-4 md:p-8 text-center text-gray-400">불러오는 중...</div>
    );
  }

  return (
    <div className="p-4 md:p-8 max-w-2xl">
      <h1 className="text-2xl font-bold mb-2">🌅 나의 다짐</h1>
      <p className="text-sm text-gray-500 mb-6">
        여기에 적은 다짐을 매일 트렌드레터와 함께 텔레그램으로 보내드려요. 한 줄에
        하나씩 적어보세요.
      </p>

      <section className="bg-white p-5 rounded-xl border mb-4">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={10}
          placeholder={"술 안 먹기\n매일 30분 운동하기\n책 10페이지 읽기"}
          className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
        />
        <p className="text-xs text-gray-400 mt-2">
          빈 칸으로 저장하면 다짐 발송을 끕니다. (텔레그램 발송이 켜져 있어야
          받아볼 수 있어요)
        </p>
      </section>

      <button
        onClick={handleSave}
        disabled={saving}
        className="w-full py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 disabled:opacity-50"
      >
        {saving ? "저장 중..." : saved ? "저장 완료!" : "저장"}
      </button>
    </div>
  );
}
