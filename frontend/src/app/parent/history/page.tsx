"use client";

import { useEffect, useState } from "react";
import { listChildren, getStoryHistory } from "@/services/api";
import type { Child, StoryHistoryItem } from "@/types";

export default function HistoryPage() {
  const [children, setChildren] = useState<Child[]>([]);
  const [selectedChild, setSelectedChild] = useState<number | null>(null);
  const [stories, setStories] = useState<StoryHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);

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

  useEffect(() => {
    if (!selectedChild) return;
    const load = async () => {
      try {
        const res = await getStoryHistory(selectedChild);
        setStories(res.data.data);
      } catch { /* ignore */ }
    };
    load();
  }, [selectedChild]);

  if (loading) return <div className="flex h-64 items-center justify-center text-gray-500">加载中...</div>;

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-gray-800">故事历史</h1>

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

      {stories.length === 0 ? (
        <div className="rounded-xl bg-white p-12 text-center shadow-sm">
          <div className="mb-3 text-5xl">📖</div>
          <p className="text-gray-500">还没有故事记录</p>
        </div>
      ) : (
        <div className="space-y-3">
          {stories.map((s) => (
            <div key={s.id} className="flex items-center gap-4 rounded-xl bg-white p-4 shadow-sm">
              <div className="text-3xl">📖</div>
              <div className="flex-1">
                <h3 className="font-semibold text-gray-800">{s.title || "未命名故事"}</h3>
                <div className="mt-0.5 flex gap-2 text-xs text-gray-500">
                  <span>主题: {s.theme}</span>
                  <span>·</span>
                  <span>主角: {s.main_character}</span>
                  <span>·</span>
                  <span>场景: {s.scene}</span>
                </div>
                <div className="mt-1 text-xs text-gray-400">
                  {new Date(s.created_at).toLocaleString("zh-CN")}
                </div>
              </div>
              <span
                className={`rounded-full px-3 py-1 text-xs font-medium ${
                  s.story_status === "completed"
                    ? "bg-green-50 text-green-600"
                    : "bg-yellow-50 text-yellow-600"
                }`}
              >
                {s.story_status === "completed" ? "已完成" : "进行中"}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
