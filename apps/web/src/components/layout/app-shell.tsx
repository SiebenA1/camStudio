"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Camera, FolderKanban, LogOut, SlidersHorizontal, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/store/auth";

const NAV = [
  { href: "/projects", label: "项目中心", icon: FolderKanban },
  { href: "/equipment", label: "设备配置", icon: Camera },
  { href: "/models", label: "模型配置", icon: SlidersHorizontal },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <div className="flex min-h-screen">
      <aside className="fixed inset-y-0 left-0 z-30 flex w-60 flex-col border-r bg-card">
        <div className="flex h-14 items-center gap-2 border-b px-5">
          <Sparkles className="h-5 w-5 text-primary" />
          <span className="text-sm font-semibold">RealFrame Studio</span>
        </div>
        <nav className="flex-1 space-y-1 p-3">
          {NAV.map((item) => {
            const active = pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  active
                    ? "bg-accent text-accent-foreground"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                )}
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="border-t p-3">
          <div className="mb-2 px-1 text-sm">
            <div className="font-medium truncate">{user?.name ?? "用户"}</div>
            <div className="text-xs text-muted-foreground truncate">{user?.email}</div>
          </div>
          <button
            onClick={() => {
              logout();
              window.location.href = "/login";
            }}
            className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground"
          >
            <LogOut className="h-4 w-4" /> 退出登录
          </button>
        </div>
      </aside>
      <main className="ml-60 flex-1 p-6">{children}</main>
    </div>
  );
}
