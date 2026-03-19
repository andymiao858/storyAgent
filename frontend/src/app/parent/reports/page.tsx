"use client";

import { useEffect, useState } from "react";
import { listChildren, getLatestReport } from "@/services/api";
import type { Child, GrowthReport } from "@/types";

export default function ReportsPage() {
  const [children, setChildren] = useState<Child[]>([]);
  const [selectedChild, setSelectedChild] = useState<number | null>(null);
  const [report, setReport] = useState<GrowthReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await listChildren();
        setChildren(res.data.data);
        if (res.data.data.length > 0) {
          setSelectedChild(res.data.data[0].id);
        }
      } catch { /* ignore */ }
      setLoading(false);
    };
    load();
  }, []);

  const loadReport = async (childId: number) => {
    setGenerating(true);
    setReport(null);
    try {
      const res = await getLatestReport(childId);
      setReport(res.data.data);
    } catch { /* ignore */ }
    setGenerating(false);
  };

  useEffect(() => {
    if (selectedChild) {
      loadReport(selectedChild);
    }
  }, [selectedChild]);

  if (loading) return <div className="flex h-64 items-center justify-center text-gray-500">加载中...</div>;

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-gray-800">成长报告</h1>

      {children.length > 1 && (
        <div className="mb-4 flex gap-2">
          {children.map((child) => (
            <button
              key={child.id}
              onClick={() => setSelectedChild(child.id)}
              className={`rounded-full px-4 py-1.5 text-sm transition ${
                selectedChild === child.id
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              {child.avatar_url || "🧒"} {child.nickname}
            </button>
          ))}
        </div>
      )}

      {generating ? (
        <div className="flex h-48 items-center justify-center rounded-xl bg-white shadow-sm">
          <div className="text-center">
            <div className="mb-2 text-4xl animate-bounce">📊</div>
            <p className="text-gray-500">正在生成成长报告...</p>
          </div>
        </div>
      ) : report ? (
        <div className="space-y-4">
          <div className="rounded-xl bg-white p-6 shadow-sm">
            <h3 className="mb-3 text-lg font-semibold text-gray-800">成长总结</h3>
            <p className="leading-relaxed text-gray-700">{report.summary}</p>
          </div>

          {report.behavior_tags && report.behavior_tags.length > 0 && (
            <div className="rounded-xl bg-white p-6 shadow-sm">
              <h3 className="mb-3 text-lg font-semibold text-gray-800">品质标签</h3>
              <div className="flex flex-wrap gap-2">
                {report.behavior_tags.map((tag) => (
                  <span
                    key={tag}
                    className="rounded-full bg-gradient-to-r from-blue-100 to-purple-100 px-4 py-1.5 text-sm font-medium text-blue-700"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="rounded-xl bg-gradient-to-r from-amber-50 to-orange-50 p-6 shadow-sm">
            <h3 className="mb-3 text-lg font-semibold text-amber-800">亲子建议</h3>
            <p className="leading-relaxed text-amber-700">{report.recommendations}</p>
          </div>

          <div className="text-right text-xs text-gray-400">
            报告生成时间：{report.report_date ? new Date(report.report_date).toLocaleString("zh-CN") : ""}
          </div>
        </div>
      ) : (
        <div className="rounded-xl bg-white p-12 text-center shadow-sm">
          <div className="mb-3 text-5xl">📊</div>
          <p className="text-gray-500">暂无成长报告</p>
          <p className="mt-1 text-sm text-gray-400">孩子完成故事后即可生成成长报告</p>
        </div>
      )}
    </div>
  );
}
