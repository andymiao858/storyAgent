"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { listChildren } from "@/services/api";
import { useAuthStore } from "@/store/auth";
import { useChildStore } from "@/store/child";
import type { Child } from "@/types";

export default function ChildSelectPage() {
  const [children, setChildren] = useState<Child[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const { loadFromStorage, token } = useAuthStore();
  const { setCurrentChild } = useChildStore();

  useEffect(() => {
    loadFromStorage();
  }, [loadFromStorage]);

  useEffect(() => {
    if (!token) return;
    const load = async () => {
      try {
        const res = await listChildren();
        setChildren(res.data.data);
      } catch { /* ignore */ }
      setLoading(false);
    };
    load();
  }, [token]);

  const handleSelect = (child: Child) => {
    setCurrentChild(child);
    router.push("/child/home");
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-yellow-100 to-pink-100">
        <p className="text-xl text-gray-600">加载中...</p>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-yellow-100 via-pink-50 to-blue-100 p-6">
      <h1 className="mb-2 text-4xl font-bold text-purple-700">你好呀！</h1>
      <p className="mb-10 text-xl text-purple-500">选择你的头像开始冒险吧</p>

      <div className="flex flex-wrap justify-center gap-6">
        {children.map((child) => (
          <button
            key={child.id}
            onClick={() => handleSelect(child)}
            className="group flex flex-col items-center rounded-3xl bg-white p-6 shadow-lg transition hover:scale-105 hover:shadow-xl"
          >
            <div className="mb-3 text-7xl transition group-hover:scale-110">
              {child.avatar_url || "🧒"}
            </div>
            <div className="text-xl font-bold text-gray-800">{child.nickname}</div>
            <div className="mt-1 text-sm text-gray-400">{child.age}岁</div>
          </button>
        ))}
      </div>

      {children.length === 0 && (
        <div className="text-center">
          <div className="mb-4 text-6xl">😿</div>
          <p className="text-lg text-gray-600">还没有小朋友的账号</p>
          <p className="mt-2 text-gray-400">请让爸爸妈妈先创建一个吧</p>
        </div>
      )}

      <button
        onClick={() => router.push("/parent")}
        className="mt-10 rounded-full bg-white px-6 py-2 text-sm text-gray-500 shadow-sm hover:bg-gray-50"
      >
        返回家长模式
      </button>
    </div>
  );
}
