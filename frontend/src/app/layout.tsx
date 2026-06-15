import type { Metadata } from "next";
import "./globals.css";
import NavBar from "@/components/NavBar";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000"),
  title: {
    default: "探球 - 2026 世界杯 AI 足球情报平台",
    template: "%s | 探球",
  },
  description: "探球提供 2026 世界杯赛程、实时比赛、阵型可视化、AI 解说、战术分析与足球知识库。",
  keywords: ["探球", "2026 世界杯", "足球 AI", "比赛分析", "战术分析", "阵型可视化"],
  openGraph: {
    title: "探球 - 2026 世界杯 AI 足球情报平台",
    description: "赛前洞察、实时分析、阵型可视化与 AI 足球情报。",
    siteName: "探球",
    locale: "zh_CN",
    type: "website",
    images: [
      {
        url: "/images/tanqiu-logo-preview.png",
        width: 1600,
        height: 900,
        alt: "探球 Logo",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "探球 - 2026 世界杯 AI 足球情报平台",
    description: "赛前洞察、实时分析、阵型可视化与 AI 足球情报。",
    images: ["/images/tanqiu-logo-preview.png"],
  },
};

function Footer() {
  return (
    <footer style={{ background: 'var(--card-bg)', borderTop: '1px solid var(--card-border)', marginTop: 'auto' }}>
      <div className="container-responsive py-8">
        <div className="flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="text-center md:text-left">
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
              探球 - 数据驱动的 AI 足球情报平台
            </p>
          </div>
          <div className="flex items-center gap-6">
            <span className="badge badge-primary">解说</span>
            <span className="badge badge-accent">可视化</span>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body className="min-h-full flex flex-col gradient-bg">
        <NavBar />
        <main className="flex-1">
          {children}
        </main>
        <Footer />
      </body>
    </html>
  );
}
