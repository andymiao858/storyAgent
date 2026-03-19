"use client";

import { useEffect, useState } from "react";
import { listChildren, createChild, updateChild } from "@/services/api";
import type { Child } from "@/types";

const avatarOptions = ["🧒", "👦", "👧", "🧒🏻", "👦🏽", "👧🏻", "🐰", "🦊", "🐻", "🐼", "🦁", "🐱"];
const readingLevels = [
  { value: "beginner", label: "入门" },
  { value: "intermediate", label: "中级" },
  { value: "advanced", label: "高级" },
];

export default function ChildrenManagePage() {
  const [children, setChildren] = useState<Child[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState({
    nickname: "",
    age: 5,
    avatar_url: "🧒",
    interests: "" as string,
    reading_level: "beginner",
  });
  const [saving, setSaving] = useState(false);

  const loadChildren = async () => {
    try {
      const res = await listChildren();
      setChildren(res.data.data);
    } catch { /* ignore */ }
    setLoading(false);
  };

  useEffect(() => {
    loadChildren();
  }, []);

  const resetForm = () => {
    setForm({ nickname: "", age: 5, avatar_url: "🧒", interests: "", reading_level: "beginner" });
    setEditingId(null);
    setShowForm(false);
  };

  const handleEdit = (child: Child) => {
    setForm({
      nickname: child.nickname,
      age: child.age,
      avatar_url: child.avatar_url || "🧒",
      interests: (child.interests || []).join("、"),
      reading_level: child.reading_level,
    });
    setEditingId(child.id);
    setShowForm(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const data = {
        nickname: form.nickname,
        age: form.age,
        avatar_url: form.avatar_url,
        interests: form.interests.split(/[、,，]/).map((s) => s.trim()).filter(Boolean),
        reading_level: form.reading_level,
      };
      if (editingId) {
        await updateChild(editingId, data);
      } else {
        await createChild(data);
      }
      resetForm();
      await loadChildren();
    } catch { /* ignore */ }
    setSaving(false);
  };

  if (loading) return <div className="flex h-64 items-center justify-center text-gray-500">加载中...</div>;

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">儿童档案管理</h1>
        <button
          onClick={() => { resetForm(); setShowForm(true); }}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          + 添加儿童
        </button>
      </div>

      {showForm && (
        <div className="mb-6 rounded-xl bg-white p-6 shadow-sm">
          <h3 className="mb-4 text-lg font-semibold">{editingId ? "编辑儿童档案" : "创建儿童档案"}</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">选择头像</label>
              <div className="flex flex-wrap gap-2">
                {avatarOptions.map((av) => (
                  <button
                    key={av}
                    type="button"
                    onClick={() => setForm({ ...form, avatar_url: av })}
                    className={`rounded-lg p-2 text-2xl transition ${
                      form.avatar_url === av ? "bg-blue-100 ring-2 ring-blue-500" : "bg-gray-50 hover:bg-gray-100"
                    }`}
                  >
                    {av}
                  </button>
                ))}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">昵称</label>
                <input
                  value={form.nickname}
                  onChange={(e) => setForm({ ...form, nickname: e.target.value })}
                  required
                  className="w-full rounded-lg border px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 focus:outline-none"
                  placeholder="宝贝的昵称"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">年龄</label>
                <input
                  type="number"
                  min={2}
                  max={12}
                  value={form.age}
                  onChange={(e) => setForm({ ...form, age: parseInt(e.target.value) || 5 })}
                  className="w-full rounded-lg border px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 focus:outline-none"
                />
              </div>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">兴趣爱好（用顿号分隔）</label>
              <input
                value={form.interests}
                onChange={(e) => setForm({ ...form, interests: e.target.value })}
                className="w-full rounded-lg border px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 focus:outline-none"
                placeholder="例如：太空、恐龙、海洋"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">阅读水平</label>
              <div className="flex gap-3">
                {readingLevels.map((lv) => (
                  <button
                    key={lv.value}
                    type="button"
                    onClick={() => setForm({ ...form, reading_level: lv.value })}
                    className={`rounded-lg px-4 py-2 text-sm transition ${
                      form.reading_level === lv.value
                        ? "bg-blue-600 text-white"
                        : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                    }`}
                  >
                    {lv.label}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex gap-3">
              <button
                type="submit"
                disabled={saving}
                className="rounded-lg bg-blue-600 px-6 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {saving ? "保存中..." : "保存"}
              </button>
              <button
                type="button"
                onClick={resetForm}
                className="rounded-lg bg-gray-100 px-6 py-2 text-sm text-gray-700 hover:bg-gray-200"
              >
                取消
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {children.map((child) => (
          <div key={child.id} className="rounded-xl bg-white p-5 shadow-sm">
            <div className="mb-3 flex items-start justify-between">
              <div className="text-5xl">{child.avatar_url || "🧒"}</div>
              <button
                onClick={() => handleEdit(child)}
                className="rounded-lg bg-gray-50 px-3 py-1 text-xs text-gray-600 hover:bg-gray-100"
              >
                编辑
              </button>
            </div>
            <h3 className="text-lg font-semibold text-gray-800">{child.nickname}</h3>
            <p className="text-sm text-gray-500">{child.age}岁 · {readingLevels.find((l) => l.value === child.reading_level)?.label || child.reading_level}</p>
            <div className="mt-2 flex flex-wrap gap-1">
              {(child.interests || []).map((i) => (
                <span key={i} className="rounded-full bg-blue-50 px-2 py-0.5 text-xs text-blue-600">
                  {i}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>

      {children.length === 0 && !showForm && (
        <div className="rounded-xl bg-white p-12 text-center shadow-sm">
          <div className="mb-3 text-5xl">👶</div>
          <p className="text-gray-500">还没有儿童档案</p>
          <p className="mt-1 text-sm text-gray-400">点击上方"添加儿童"按钮创建第一个儿童账号</p>
        </div>
      )}
    </div>
  );
}
