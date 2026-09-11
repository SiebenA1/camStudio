"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/store/auth";
import { api } from "@/lib/api";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { token, user, loaded, init, setUser, logout } = useAuth();

  useEffect(() => {
    init();
  }, [init]);

  // 未登录 → 跳转登录页
  useEffect(() => {
    if (loaded && !token) router.replace("/login");
  }, [loaded, token, router]);

  // 有 token 但无用户信息 → 拉取 /me
  useEffect(() => {
    if (loaded && token && !user) {
      api
        .get<{ id: string }>("/auth/me")
        .then((u) => setUser(u as never))
        .catch(() => {
          logout();
          router.replace("/login");
        });
    }
  }, [loaded, token, user, setUser, logout, router]);

  if (!loaded || !token) {
    return <div className="flex min-h-screen items-center justify-center text-muted-foreground">加载中…</div>;
  }
  return <>{children}</>;
}
