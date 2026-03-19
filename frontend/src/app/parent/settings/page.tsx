"use client";

import { useEffect, useState } from "react";
import { getParentSettings, updateParentSettings } from "@/services/api";

export default function SettingsPage() {
  const [blockedTopics, setBlockedTopics] = useState("");
  const [preferredThemes, setPreferredThemes] = useState("");
  const [dailyLimit, setDailyLimit] = useState(60);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await getParentSettings();
        const data = res.data.data;
        setBlockedTopics((data.blocked_topics || []).join("、"));
        setPreferredThemes((data.preferred_themes || []).join("、"));
        setDailyLimit(data.daily_limit_minutes || 60);
      } catch { /* ignore */ }
      setLoading(false);
    };
    load();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    try {
      await updateParentSettings({
        blocked_topics: blockedTopics.split(/[、,，]/).map((s) => s.trim()).filter(Boolean),
        preferred_themes: preferredThemes.split(/[、,，]/).map((s) => s.trim()).filter(Boolean),
        daily_limit_minutes: dailyLimit,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch { /* ignore */ }
    setSaving(false);
  };

  if (loading) return <div className="flex h-64 items-center justify-center text-gray-500">加载中...</div>;

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-gray-800">安全与偏好设置</h1>

      <div className="max-w-xl space-y-6 rounded-xl bg-white p-6 shadow-sm">
        <div>
          <label className="mb-2 block text-sm font-medium text-gray-700">屏蔽主题</label>
          <input
            value={blockedTopics}
            onChange={(e) => setBlockedTopics(e.target.value)}
            className="w-full rounded-lg border px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 focus:outline-none"
            placeholder="例如：恐怖、暴力、战争（用顿号分隔）"
          />
          <p className="mt-1 text-xs text-gray-400">这些主题将不会出现在故事内容中</p>
        </div>

        <div>
          <label className="mb-2 block text-sm font-medium text-gray-700">偏好主题</label>
          <input
            value={preferredThemes}
            onChange={(e) => setPreferredThemes(e.target.value)}
            className="w-full rounded-lg border px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 focus:outline-none"
            placeholder="例如：探险、合作、勇敢（用顿号分隔）"
          />
          <p className="mt-1 text-xs text-gray-400">系统会优先推荐相关主题的故事</p>
        </div>

        <div>
          <label className="mb-2 block text-sm font-medium text-gray-700">每日使用时长限制</label>
          <div className="flex items-center gap-3">
            <input
              type="range"
              min={15}
              max={120}
              step={15}
              value={dailyLimit}
              onChange={(e) => setDailyLimit(parseInt(e.target.value))}
              className="flex-1"
            />
            <span className="w-20 text-center font-semibold text-gray-800">{dailyLimit} 分钟</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleSave}
            disabled={saving}
            className="rounded-lg bg-blue-600 px-6 py-2.5 font-medium text-white transition hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? "保存中..." : "保存设置"}
          </button>
          {saved && <span className="text-sm text-green-600">已保存</span>}
        </div>
      </div>
    </div>
  );
}
