"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useChildStore } from "@/store/child";
import { useAuthStore } from "@/store/auth";

const themes = [
  { value: "探险", icon: "🗺️", color: "from-amber-400 to-orange-500" },
  { value: "魔法", icon: "🪄", color: "from-purple-400 to-pink-500" },
  { value: "太空", icon: "🚀", color: "from-blue-400 to-indigo-500" },
  { value: "海洋", icon: "🌊", color: "from-cyan-400 to-blue-500" },
  { value: "合作", icon: "🤝", color: "from-green-400 to-emerald-500" },
  { value: "勇敢", icon: "🦁", color: "from-red-400 to-pink-500" },
];

const characters = [
  { value: "勇敢小兔", icon: "🐰" },
  { value: "聪明小狐", icon: "🦊" },
  { value: "太空探险家", icon: "🧑‍🚀" },
  { value: "小美人鱼", icon: "🧜‍♀️" },
  { value: "魔法猫咪", icon: "🐱" },
  { value: "友善小熊", icon: "🐻" },
];

const scenes = [
  { value: "森林", icon: "🌲" },
  { value: "海底世界", icon: "🐠" },
  { value: "太空站", icon: "🛸" },
  { value: "魔法学校", icon: "🏫" },
  { value: "小镇", icon: "🏘️" },
  { value: "农场", icon: "🌾" },
];

export default function StoryConfigPage() {
  const [selectedTheme, setSelectedTheme] = useState("");
  const [selectedCharacter, setSelectedCharacter] = useState("");
  const [selectedScene, setSelectedScene] = useState("");
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1);
  const router = useRouter();
  const { currentChild, loadFromStorage: loadChild } = useChildStore();
  const { loadFromStorage: loadAuth } = useAuthStore();

  useEffect(() => {
    loadAuth();
    loadChild();
  }, [loadAuth, loadChild]);

  useEffect(() => {
    if (typeof window !== "undefined" && !currentChild) {
      const str = localStorage.getItem("currentChild");
      if (!str) router.push("/child/select");
    }
  }, [currentChild, router]);

  const handleStart = () => {
    if (!currentChild) return;
    setLoading(true);
    const params = new URLSearchParams({
      newStory: "1",
      childId: String(currentChild.id),
      theme: selectedTheme,
      character: selectedCharacter,
      scene: selectedScene,
    });
    router.push(`/child/story?${params.toString()}`);
  };

  if (!currentChild) return null;

  return (
    <div className="min-h-screen bg-gradient-to-b from-yellow-100 via-pink-50 to-blue-100 p-6">
      <div className="mx-auto max-w-lg">
        <button
          onClick={() => router.push("/child/home")}
          className="mb-4 text-sm text-gray-500 hover:text-gray-700"
        >
          ← 返回首页
        </button>

        <div className="mb-6 text-center">
          <h1 className="text-3xl font-bold text-purple-700">创建你的故事</h1>
          <p className="mt-1 text-purple-400">第 {step} 步，共 3 步</p>
          <div className="mx-auto mt-3 flex w-48 gap-1">
            {[1, 2, 3].map((s) => (
              <div
                key={s}
                className={`h-2 flex-1 rounded-full transition ${
                  s <= step ? "bg-purple-500" : "bg-purple-200"
                }`}
              />
            ))}
          </div>
        </div>

        {step === 1 && (
          <div>
            <h2 className="mb-4 text-center text-xl font-bold text-gray-700">选择故事主题</h2>
            <div className="grid grid-cols-2 gap-3">
              {themes.map((t) => (
                <button
                  key={t.value}
                  onClick={() => { setSelectedTheme(t.value); setStep(2); }}
                  className={`rounded-2xl bg-gradient-to-br ${t.color} p-5 text-center text-white shadow-md transition hover:scale-105 hover:shadow-lg ${
                    selectedTheme === t.value ? "ring-4 ring-white ring-offset-2" : ""
                  }`}
                >
                  <div className="mb-1 text-4xl">{t.icon}</div>
                  <div className="text-lg font-bold">{t.value}</div>
                </button>
              ))}
            </div>
          </div>
        )}

        {step === 2 && (
          <div>
            <h2 className="mb-4 text-center text-xl font-bold text-gray-700">选择故事主角</h2>
            <div className="grid grid-cols-2 gap-3">
              {characters.map((c) => (
                <button
                  key={c.value}
                  onClick={() => { setSelectedCharacter(c.value); setStep(3); }}
                  className={`rounded-2xl bg-white p-5 text-center shadow-md transition hover:scale-105 hover:shadow-lg ${
                    selectedCharacter === c.value ? "ring-4 ring-purple-400" : ""
                  }`}
                >
                  <div className="mb-1 text-5xl">{c.icon}</div>
                  <div className="font-bold text-gray-800">{c.value}</div>
                </button>
              ))}
            </div>
            <button onClick={() => setStep(1)} className="mx-auto mt-4 block text-sm text-gray-500">
              ← 上一步
            </button>
          </div>
        )}

        {step === 3 && (
          <div>
            <h2 className="mb-4 text-center text-xl font-bold text-gray-700">选择故事场景</h2>
            <div className="grid grid-cols-2 gap-3">
              {scenes.map((s) => (
                <button
                  key={s.value}
                  onClick={() => setSelectedScene(s.value)}
                  className={`rounded-2xl bg-white p-5 text-center shadow-md transition hover:scale-105 hover:shadow-lg ${
                    selectedScene === s.value ? "ring-4 ring-purple-400" : ""
                  }`}
                >
                  <div className="mb-1 text-5xl">{s.icon}</div>
                  <div className="font-bold text-gray-800">{s.value}</div>
                </button>
              ))}
            </div>

            {selectedScene && (
              <div className="mt-6">
                <div className="mb-4 rounded-2xl bg-white/80 p-4 text-center backdrop-blur">
                  <p className="text-sm text-gray-500">你的故事设定</p>
                  <p className="mt-1 text-lg font-bold text-gray-800">
                    {selectedCharacter} 在 {selectedScene} 的 {selectedTheme} 故事
                  </p>
                </div>
                <button
                  onClick={handleStart}
                  disabled={loading}
                  className="w-full rounded-2xl bg-gradient-to-r from-purple-500 to-pink-500 py-4 text-xl font-bold text-white shadow-lg transition hover:scale-[1.02] hover:shadow-xl disabled:opacity-50"
                >
                  {loading ? "故事正在生成..." : "开始冒险！✨"}
                </button>
              </div>
            )}

            <button onClick={() => setStep(2)} className="mx-auto mt-4 block text-sm text-gray-500">
              ← 上一步
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
