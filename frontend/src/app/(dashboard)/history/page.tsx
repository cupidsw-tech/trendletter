"use client";

import { useEffect, useState } from "react";

interface LogItem {
  id: string;
  channel: string;
  status: string;
  sentAt: string | null;
  createdAt: string;
  article: { title: string };
}

const CHANNEL_LABELS: Record<string, string> = {
  web: "웹",
  telegram: "텔레그램",
  kakao: "카카오톡",
};

const STATUS_STYLES: Record<string, string> = {
  sent: "bg-green-50 text-green-700",
  pending: "bg-yellow-50 text-yellow-700",
  failed: "bg-red-50 text-red-700",
};

export default function HistoryPage() {
  const [logs, setLogs] = useState<LogItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/delivery")
      .then((r) => r.json())
      .then((data) => {
        setLogs(data);
        setLoading(false);
      });
  }, []);

  return (
    <div className="p-4 md:p-8 max-w-4xl">
      <h1 className="text-2xl font-bold mb-6">발송 이력</h1>

      {loading ? (
        <div className="text-center py-12 text-gray-400">불러오는 중...</div>
      ) : logs.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl border">
          <p className="text-gray-500">발송 이력이 없습니다</p>
        </div>
      ) : (
        <div className="space-y-2">
          {logs.map((log) => (
            <div
              key={log.id}
              className="bg-white p-4 rounded-xl border flex items-center gap-3"
            >
              <span
                className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                  STATUS_STYLES[log.status] || "bg-gray-100 text-gray-600"
                }`}
              >
                {log.status === "sent"
                  ? "발송완료"
                  : log.status === "pending"
                  ? "대기중"
                  : "실패"}
              </span>
              <span className="text-xs text-gray-400">
                {CHANNEL_LABELS[log.channel] || log.channel}
              </span>
              <span className="text-sm font-medium flex-1 truncate">
                {log.article.title}
              </span>
              <span className="text-xs text-gray-300">
                {new Date(log.createdAt).toLocaleString("ko-KR")}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
