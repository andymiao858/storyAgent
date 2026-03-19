"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { listChildren, getStoryHistory } from "@/services/api";
import type { Child, StoryHistoryItem } from "@/types";

export default function ParentDashboard() {
  const [children, setChildren] = useState<Child[]>([]);
  const [recentStories, setRecentStories] = useState<StoryHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const load = async () => {
      try {
        const res = await listChildren();
        const kids = res.data.data;
        setChildren(kids);

        const allStories: StoryHistoryItem[] = [];
        for (const kid of kids.slice(0, 5)) {
          try {
            const histRes = await getStoryHistory(kid.id);
            allStories.push(...histRes.data.data.slice(0, 3));
          } catch { /* ignore */ }
        }
        allStories.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
        setRecentStories(allStories.slice(0, 5));
      } catch { /* ignore */ }
      setLoading(false);
    };
    load();
  }, []);

  if (loading) {
    return <div className="flex h-64 items-center justify-center text-gray-500">加载中...</div>;
  }

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-gray-800">家长控制台</h1>

      <div className="mb-8 grid grid-cols-1 gap-4 md:grid-cols-3">
        <div className="rounded-xl bg-white p-5 shadow-sm">
          <div className="mb-2 text-3xl">👶</div>
          <div className="text-2xl font-bold text-gray-800">{children.length}</div>
          <div className="text-sm text-gray-500">儿童账号</div>
        </div>
        <div className="rounded-xl bg-white p-5 shadow-sm">
          <div className="mb-2 text-3xl">📖</div>
          <div className="text-2xl font-bold text-gray-800">{recentStories.length}</div>
          <div className="text-sm text-gray-500">近期故事</div>
        </div>
        <div
          onClick={() => router.push("/child/select")}
          className="cursor-pointer rounded-xl bg-gradient-to-r from-green-400 to-emerald-500 p-5 text-white shadow-sm transition hover:shadow-md"
        >
          <div className="mb-2 text-3xl">🎮</div>
          <div className="text-lg font-bold">进入儿童模式</div>
          <div className="text-sm opacity-90">让孩子开始故事冒险</div>
        </div>
      </div>

      <div className="mb-8">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-700">儿童列表</h2>
          <button
            onClick={() => router.push("/parent/children")}
            className="text-sm text-blue-600 hover:underline"
          >
            管理 →
          </button>
        </div>
        {children.length === 0 ? (
          <div className="rounded-xl bg-white p-8 text-center shadow-sm">
            <p className="text-gray-500">还没有创建儿童账号</p>
            <button
              onClick={() => router.push("/parent/children")}
              className="mt-3 rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
            >
              创建儿童账号
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
            {children.map((child) => (
              <div key={child.id} className="rounded-xl bg-white p-4 shadow-sm">
                <div className="mb-2 text-4xl">{child.avatar_url || "🧒"}</div>
                <div className="font-medium text-gray-800">{child.nickname}</div>
                <div className="text-sm text-gray-500">{child.age}岁 · {child.reading_level}</div>
                <div className="mt-1 flex flex-wrap gap-1">
                  {(child.interests || []).map((i) => (
                    <span key={i} className="rounded-full bg-blue-50 px-2 py-0.5 text-xs text-blue-600">
                      {i}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {recentStories.length > 0 && (
        <div>
          <h2 className="mb-3 text-lg font-semibold text-gray-700">近期故事</h2>
          <div className="space-y-2">
            {recentStories.map((s) => (
              <div key={s.id} className="flex items-center gap-3 rounded-xl bg-white p-3 shadow-sm">
                <div className="text-2xl">📖</div>
                <div className="flex-1">
                  <div className="font-medium text-gray-800">{s.title || "未命名故事"}</div>
                  <div className="text-xs text-gray-500">
                    {s.theme} · {s.main_character} · {s.scene}
                  </div>
                </div>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs ${
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
        </div>
      )}
    </div>
  );
}
