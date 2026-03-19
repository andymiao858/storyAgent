import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI儿童故事系统",
  description: "基于AI的个性化儿童故事生成与互动系统",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen bg-gray-50 antialiased">{children}</body>
    </html>
  );
}
