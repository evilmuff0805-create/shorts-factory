"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", label: "트렌드 추천" },
  { href: "/create", label: "영상 생성" },
  { href: "/batch", label: "일괄 생성" },
  { href: "/convert", label: "롱비디오 변환" },
  { href: "/news", label: "뉴스 숏츠" },
  { href: "/article", label: "기사 분석" },
  { href: "/settings", label: "설정" },
];

export default function Sidebar() {
  const pathname = usePathname() ?? "/";

  return (
    <aside className="w-60 shrink-0 bg-sidebar border-r border-sidebar-border flex flex-col min-h-screen">
      <div className="px-6 py-5 border-b border-sidebar-border">
        <h1 className="text-lg font-bold text-sidebar-foreground">Shorts Factory</h1>
      </div>
      <nav className="flex-1 py-4 px-3">
        <ul className="space-y-1">
          {navItems.map((item) => (
            <li key={item.href}>
              <Link
                href={item.href}
                className={cn(
                  "block px-3 py-2 rounded-md text-sm font-medium transition-colors",
                  pathname === item.href
                    ? "bg-sidebar-primary text-sidebar-primary-foreground"
                    : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                )}
              >
                {item.label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
}
