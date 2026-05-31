"use client";

import { useEffect, useState } from "react";

export default function SettingsPage() {
  const [settings, setSettings] = useState({
    deliverWeb: true,
    deliverTelegram: false,
    deliverKakao: false,
    telegramChatId: "",
    templateId: "compact",
    scheduleHour: 8,
    scheduleMinute: 0,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    fetch("/api/settings")
      .then((r) => r.json())
      .then((data) => {
        setSettings(data);
        setLoading(false);
      });
  }, []);

  async function handleSave() {
    setSaving(true);
    setSaved(false);
    await fetch("/api/settings", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings),
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
      <h1 className="text-2xl font-bold mb-6">설정</h1>

      {/* 발송 시간 */}
      <section className="bg-white p-5 rounded-xl border mb-4">
        <h2 className="font-semibold mb-3">발송 시간</h2>
        <p className="text-sm text-gray-500 mb-3">
          매일 이 시간에 등록된 URL을 크롤링하고 요약을 발송합니다
        </p>
        <div className="flex items-center gap-2">
          <select
            value={settings.scheduleHour}
            onChange={(e) =>
              setSettings({ ...settings, scheduleHour: Number(e.target.value) })
            }
            className="px-3 py-2 border rounded-lg text-sm"
          >
            {Array.from({ length: 24 }, (_, i) => (
              <option key={i} value={i}>
                {String(i).padStart(2, "0")}시
              </option>
            ))}
          </select>
          <select
            value={settings.scheduleMinute}
            onChange={(e) =>
              setSettings({
                ...settings,
                scheduleMinute: Number(e.target.value),
              })
            }
            className="px-3 py-2 border rounded-lg text-sm"
          >
            {[0, 15, 30, 45].map((m) => (
              <option key={m} value={m}>
                {String(m).padStart(2, "0")}분
              </option>
            ))}
          </select>
          <span className="text-sm text-gray-400">(한국 시간)</span>
        </div>
      </section>

      {/* 뉴스레터 템플릿 */}
      <section className="bg-white p-5 rounded-xl border mb-4">
        <h2 className="font-semibold mb-3">뉴스레터 스타일</h2>
        <p className="text-sm text-gray-500 mb-3">
          발송되는 뉴스레터의 형식을 선택하세요
        </p>
        <div className="grid grid-cols-2 gap-2">
          {[
            { id: "compact", name: "📋 간결한 요약", desc: "핵심만 불릿 포인트로" },
            { id: "detailed", name: "📊 상세 리포트", desc: "섹션별 상세 분석" },
            { id: "morning_brief", name: "☀️ 모닝 브리프", desc: "한눈에 보는 트렌드" },
            { id: "card_news", name: "🃏 카드뉴스", desc: "한 줄 제목 + 핵심" },
          ].map((tmpl) => (
            <button
              key={tmpl.id}
              onClick={() => setSettings({ ...settings, templateId: tmpl.id })}
              className={`p-3 rounded-lg border text-left transition-colors ${
                settings.templateId === tmpl.id
                  ? "border-blue-500 bg-blue-50"
                  : "border-gray-200 hover:bg-gray-50"
              }`}
            >
              <p className="font-medium text-sm">{tmpl.name}</p>
              <p className="text-xs text-gray-400">{tmpl.desc}</p>
            </button>
          ))}
        </div>
      </section>

      {/* 발송 채널 */}
      <section className="bg-white p-5 rounded-xl border mb-4">
        <h2 className="font-semibold mb-3">발송 채널</h2>

        {/* 웹 */}
        <label className="flex items-center gap-3 p-3 hover:bg-gray-50 rounded-lg cursor-pointer">
          <input
            type="checkbox"
            checked={settings.deliverWeb}
            onChange={(e) =>
              setSettings({ ...settings, deliverWeb: e.target.checked })
            }
            className="w-4 h-4 rounded"
          />
          <div>
            <p className="font-medium text-sm">웹 대시보드</p>
            <p className="text-xs text-gray-400">
              대시보드에서 직접 확인 (모바일 바로가기 추가 가능)
            </p>
          </div>
        </label>

        {/* 텔레그램 */}
        <label className="flex items-start gap-3 p-3 hover:bg-gray-50 rounded-lg cursor-pointer">
          <input
            type="checkbox"
            checked={settings.deliverTelegram}
            onChange={(e) =>
              setSettings({
                ...settings,
                deliverTelegram: e.target.checked,
              })
            }
            className="w-4 h-4 rounded mt-0.5"
          />
          <div className="flex-1">
            <p className="font-medium text-sm">텔레그램</p>
            <p className="text-xs text-gray-400 mb-2">
              텔레그램 봇으로 요약 메시지 + PDF 전송
            </p>
            {settings.deliverTelegram && (
              <div>
                <input
                  type="text"
                  placeholder="텔레그램 Chat ID"
                  value={settings.telegramChatId || ""}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      telegramChatId: e.target.value,
                    })
                  }
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-400 mt-1">
                  @TrendLetterBot에게 /start 메시지를 보내면 Chat ID를 알 수
                  있습니다
                </p>
              </div>
            )}
          </div>
        </label>

        {/* 카카오톡 */}
        <label className="flex items-start gap-3 p-3 hover:bg-gray-50 rounded-lg cursor-pointer">
          <input
            type="checkbox"
            checked={settings.deliverKakao}
            onChange={(e) =>
              setSettings({ ...settings, deliverKakao: e.target.checked })
            }
            className="w-4 h-4 rounded mt-0.5"
          />
          <div className="flex-1">
            <p className="font-medium text-sm">카카오톡</p>
            <p className="text-xs text-gray-400 mb-2">
              카카오톡 나에게 보내기로 요약 발송
            </p>
            {settings.deliverKakao && (
              <a
                href={`https://kauth.kakao.com/oauth/authorize?client_id=${process.env.NEXT_PUBLIC_KAKAO_CLIENT_ID || "d09fecc2caa6c8a657dd4f08e9aecfb4"}&redirect_uri=${encodeURIComponent("http://localhost:3000/api/auth/kakao/callback")}&response_type=code&scope=talk_message`}
                className="inline-block px-4 py-2 bg-yellow-400 text-black rounded-lg text-sm font-medium hover:bg-yellow-500"
              >
                카카오톡 연결하기
              </a>
            )}
          </div>
        </label>
      </section>

      {/* 저장 */}
      <button
        onClick={handleSave}
        disabled={saving}
        className="w-full py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 disabled:opacity-50"
      >
        {saving ? "저장 중..." : saved ? "저장 완료!" : "설정 저장"}
      </button>
    </div>
  );
}
