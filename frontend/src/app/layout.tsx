import type { Metadata } from "next";
import "./globals.css";
import NavBar from "@/components/NavBar";

export const metadata: Metadata = {
  title: "世界杯AI助手",
  description: "足球比赛预测、AI解说、可视化分析与世界杯知识百库",
};

function Footer() {
  return (
    <footer style={{ background: 'var(--card-bg)', borderTop: '1px solid var(--card-border)', marginTop: 'auto' }}>
      <div className="container-responsive py-8">
        <div className="flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="text-center md:text-left">
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
              世界杯AI助手 - 数据驱动的人工智能足球分析平台
            </p>
          </div>
          <div className="flex items-center gap-6">
            <span className="badge badge-secondary">预测</span>
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
