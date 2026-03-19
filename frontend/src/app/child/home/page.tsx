"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useChildStore } from "@/store/child";
import { useAuthStore } from "@/store/auth";
import { getStoryHistory } from "@/services/api";
import type { StoryHistoryItem } from "@/types";

export default function ChildHomePage() {
  const router = useRouter();
  const { currentChild, loadFromStorage: loadChild } = useChildStore();
  const { loadFromStorage: loadAuth } = useAuthStore();
  const [stories, setStories] = useState<StoryHistoryItem[]>([]);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    loadAuth();
    loadChild();
    setReady(true);
  }, [loadAuth, loadChild]);

  useEffect(() => {
    if (!ready) return;
    if (!currentChild) {
      router.push("/child/select");
      return;
    }
    const load = async () => {
      try {
        const res = await getStoryHistory(currentChild.id);
        setStories(res.data.data);
      } catch { /* ignore */ }
    };
    load();
  }, [ready, currentChild, router]);

  if (!ready || !currentChild) return null;

  const ongoingStories = stories.filter((s) => s.story_status === "in_progress");
  const completedStories = stories.filter((s) => s.story_status === "completed");

  const openStory = (s: StoryHistoryItem) => {
    if (s.session_id) {
      router.push(`/child/story?sessionId=${s.session_id}`);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-100 via-purple-50 to-pink-100 p-6">
      <div className="mx-auto max-w-lg">
        <div className="mb-8 text-center">
          <div className="mb-2 text-7xl">{currentChild.avatar_url || "🧒"}</div>
          <h1 className="text-3xl font-bold text-purple-700">
            你好，{currentChild.nickname}！
          </h1>
          <p className="mt-1 text-lg text-purple-400">今天想听什么故事呢？</p>
        </div>

        <div className="space-y-4">
          {/* New story button */}
          <button
            onClick={() => router.push("/child/story-config")}
            className="flex w-full items-center gap-4 rounded-2xl bg-gradient-to-r from-orange-400 to-pink-500 p-5 text-left text-white shadow-lg transition hover:scale-[1.02] hover:shadow-xl"
          >
            <span className="text-5xl">✨</span>
            <div>
              <div className="text-xl font-bold">开始新故事</div>
              <div className="text-sm opacity-90">选择主题和角色，开启冒险！</div>
            </div>
          </button>

          {/* Continue ongoing stories */}
          {ongoingStories.map((s) => (
            <button
              key={s.id}
              onClick={() => openStory(s)}
              className="flex w-full items-center gap-4 rounded-2xl bg-gradient-to-r from-green-400 to-teal-500 p-5 text-left text-white shadow-lg transition hover:scale-[1.02] hover:shadow-xl"
            >
              <span className="text-5xl">📖</span>
              <div className="flex-1">
                <div className="text-lg font-bold">{s.title || "继续上次的故事"}</div>
                <div className="text-sm opacity-90">
                  {s.theme} · {s.main_character} · {s.scene}
                </div>
              </div>
              <span className="text-2xl">→</span>
            </button>
          ))}
        </div>

        {/* Completed stories */}
        {completedStories.length > 0 && (
          <div className="mt-8">
            <h2 className="mb-3 text-lg font-bold text-purple-600">已完成的故事</h2>
            <div className="space-y-2">
              {completedStories.slice(0, 5).map((s) => (
                <button
                  key={s.id}
                  onClick={() => openStory(s)}
                  className="flex w-full items-center gap-3 rounded-2xl bg-white/70 p-3 text-left backdrop-blur transition hover:bg-white/90"
                >
                  <span className="text-3xl">🌟</span>
                  <div className="flex-1">
                    <div className="font-medium text-gray-800">{s.title || "未命名故事"}</div>
                    <div className="text-xs text-gray-500">{s.theme} · {s.main_character}</div>
                  </div>
                  <span className="text-xs text-gray-400">查看 →</span>
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="mt-8 flex justify-center gap-4">
          <button
            onClick={() => router.push("/child/select")}
            className="rounded-full bg-white/70 px-5 py-2 text-sm text-gray-600 shadow-sm backdrop-blur hover:bg-white"
          >
            切换小朋友
          </button>
          <button
            onClick={() => router.push("/parent")}
            className="rounded-full bg-white/70 px-5 py-2 text-sm text-gray-600 shadow-sm backdrop-blur hover:bg-white"
          >
            家长模式
          </button>
        </div>
      </div>
    </div>
  );
}
