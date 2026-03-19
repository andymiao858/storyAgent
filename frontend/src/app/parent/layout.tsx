"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuthStore } from "@/store/auth";

const navItems = [
  { label: "控制台", path: "/parent", icon: "🏠" },
  { label: "儿童管理", path: "/parent/children", icon: "👶" },
  { label: "安全设置", path: "/parent/settings", icon: "🔒" },
  { label: "故事历史", path: "/parent/history", icon: "📖" },
  { label: "成长报告", path: "/parent/reports", icon: "📊" },
];

export default function ParentLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { loadFromStorage, token, user, logout } = useAuthStore();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    loadFromStorage();
    setReady(true);
  }, [loadFromStorage]);

  useEffect(() => {
    if (ready && !token) {
      router.push("/login");
    }
  }, [ready, token, router]);

  if (!ready || !token) return null;

  return (
    <div className="flex min-h-screen">
      <aside className="w-56 bg-white shadow-md">
        <div className="border-b p-4">
          <h2 className="text-lg font-bold text-gray-800">📚 故事系统</h2>
          <p className="mt-1 text-xs text-gray-500">{user?.email}</p>
        </div>
        <nav className="p-2">
          {navItems.map((item) => (
            <button
              key={item.path}
              onClick={() => router.push(item.path)}
              className={`mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-left text-sm transition ${
                pathname === item.path
                  ? "bg-blue-50 font-medium text-blue-700"
                  : "text-gray-600 hover:bg-gray-50"
              }`}
            >
              <span>{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>
        <div className="mt-auto border-t p-2">
          <button
            onClick={() => router.push("/child/select")}
            className="mb-1 flex w-full items-center gap-2 rounded-lg bg-green-50 px-3 py-2.5 text-left text-sm font-medium text-green-700 transition hover:bg-green-100"
          >
            <span>🎮</span>进入儿童模式
          </button>
          <button
            onClick={() => { logout(); router.push("/login"); }}
            className="flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-left text-sm text-gray-500 transition hover:bg-red-50 hover:text-red-600"
          >
            <span>🚪</span>退出登录
          </button>
        </div>
      </aside>
      <main className="flex-1 p-6">{children}</main>
    </div>
  );
}
