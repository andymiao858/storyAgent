"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";

export default function Home() {
  const router = useRouter();
  const { loadFromStorage, token } = useAuthStore();

  useEffect(() => {
    loadFromStorage();
  }, [loadFromStorage]);

  useEffect(() => {
    if (token) {
      router.push("/parent");
    } else {
      router.push("/login");
    }
  }, [token, router]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <div className="mb-4 text-6xl">📚</div>
        <h1 className="text-2xl font-bold text-gray-700">AI儿童故事系统</h1>
        <p className="mt-2 text-gray-500">正在加载...</p>
      </div>
    </div>
  );
}
