import "./globals.css";
import Sidebar from "@/components/Sidebar";

export const metadata = {
  title: "Shorts Factory",
  description: "YouTube Shorts 자동 생성 플랫폼",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko" className="dark">
      <body className="h-screen bg-zinc-950 text-white flex">
        <Sidebar />
        <main className="flex-1 overflow-auto">{children}</main>
      </body>
    </html>
  );
}
