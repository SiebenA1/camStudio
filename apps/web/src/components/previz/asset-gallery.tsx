"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckSquare, Download, Gauge, Loader2, MessageSquarePlus, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { api, assetUrl } from "@/lib/api";
import type { PrevizAsset, Review } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const STATUS_META: Record<string, { label: string; variant: "secondary" | "default" | "success" | "destructive" }> = {
  pending: { label: "排队中", variant: "secondary" },
  generating: { label: "生成中", variant: "default" },
  succeeded: { label: "已完成", variant: "success" },
  failed: { label: "失败", variant: "destructive" },
  superseded: { label: "已替换", variant: "secondary" },
};

function fileExt(url: string | null | undefined): string {
  const m = url?.match(/\.(\w+)(?:\?|$)/);
  return m ? m[1] : "png";
}

async function downloadAsset(a: PrevizAsset) {
  const url = assetUrl(a.file_url);
  if (!url) return;
  try {
    const res = await fetch(url);
    const blob = await res.blob();
    const objUrl = URL.createObjectURL(blob);
    const el = document.createElement("a");
    el.href = objUrl;
    el.download = `previz-${a.id.slice(0, 8)}.${fileExt(a.file_url)}`;
    document.body.appendChild(el);
    el.click();
    el.remove();
    URL.revokeObjectURL(objUrl);
  } catch {
    toast.error("下载失败");
  }
}

export function AssetGallery({ projectId }: { projectId: string }) {
  const router = useRouter();
  const qc = useQueryClient();
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const { data: assets, isLoading } = useQuery({
    queryKey: ["previz", projectId],
    queryFn: () => api.get<PrevizAsset[]>(`/projects/${projectId}/previz`),
    refetchInterval: (query) => {
      const list = query.state.data as PrevizAsset[] | undefined;
      if (list?.some((a) => a.status === "pending" || a.status === "generating")) return 3000;
      return false;
    },
  });

  const scoreMutation = useMutation({
    mutationFn: (assetId: string) => api.post<Record<string, unknown>>(`/previz/${assetId}/score`, {}),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["previz", projectId] });
      toast.success("质量评分完成");
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "评分失败"),
  });

  const deleteMutation = useMutation({
    mutationFn: (assetId: string) => api.del(`/previz/${assetId}`),
    onSuccess: () => {
      setSelected((prev) => {
        const next = new Set(prev);
        return next;
      });
      qc.invalidateQueries({ queryKey: ["previz", projectId] });
      toast.success("已删除");
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "删除失败"),
  });

  const reviewMutation = useMutation({
    mutationFn: (assetIds: string[]) =>
      api.post<Review>(`/projects/${projectId}/reviews`, { asset_ids: assetIds, type: "internal", title: "内部评审" }),
    onSuccess: (r) => {
      toast.success("评审已创建");
      router.push(`/review/${r.id}`);
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "创建评审失败"),
  });

  function toggle(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  function onDelete(a: PrevizAsset) {
    if (window.confirm(`确定删除该预演图吗？${a.error ? "（失败任务）" : ""}`)) {
      deleteMutation.mutate(a.id);
    }
  }

  if (isLoading) return <div className="text-muted-foreground">加载预演资产…</div>;

  return (
    <div>
      {selected.size > 0 && (
        <div className="mb-4 flex items-center justify-between rounded-md border bg-accent/50 px-3 py-2">
          <span className="text-sm">已选 {selected.size} 张</span>
          <Button size="sm" onClick={() => reviewMutation.mutate([...selected])} disabled={reviewMutation.isPending}>
            <MessageSquarePlus /> 创建评审
          </Button>
        </div>
      )}

      {!assets?.length ? (
        <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
          还没有预演资产，先导入 Brief 或上传空镜图生成
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
          {assets.map((a) => {
            const meta = STATUS_META[a.status] ?? { label: a.status, variant: "secondary" as const };
            const done = a.status === "succeeded";
            return (
              <div key={a.id} className={cn("group relative overflow-hidden rounded-lg border bg-card", selected.has(a.id) && "ring-2 ring-primary")}>
                <div className="relative aspect-square bg-muted">
                  {a.file_url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={assetUrl(a.file_url)} alt={a.prompt} className="h-full w-full object-cover" />
                  ) : (
                    <div className="flex h-full items-center justify-center text-muted-foreground">
                      {a.status === "failed" ? "生成失败" : <Loader2 className="h-6 w-6 animate-spin" />}
                    </div>
                  )}
                  <div className="absolute left-2 top-2">
                    <Badge variant={meta.variant}>{meta.label}</Badge>
                  </div>
                  {done && (
                    <button
                      onClick={() => toggle(a.id)}
                      className={cn(
                        "absolute right-2 top-2 rounded-md p-1",
                        selected.has(a.id) ? "bg-primary text-primary-foreground" : "bg-black/40 text-white opacity-0 group-hover:opacity-100"
                      )}
                      title="选择用于评审"
                    >
                      <CheckSquare className="h-4 w-4" />
                    </button>
                  )}
                </div>
                <div className="space-y-1 p-2">
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span className="truncate">{a.model}</span>
                    {a.quality_score != null && <span className="font-medium text-primary">{Math.round(a.quality_score)} 分</span>}
                  </div>
                  {a.error && <p className="truncate text-xs text-red-500">{a.error}</p>}
                  <div className="flex items-center gap-1">
                    {done && (
                      <Button size="sm" variant="ghost" className="flex-1" onClick={() => scoreMutation.mutate(a.id)} disabled={scoreMutation.isPending}>
                        <Gauge /> 评分
                      </Button>
                    )}
                    {done && (
                      <Button size="sm" variant="ghost" className="flex-1" onClick={() => downloadAsset(a)} title="下载到本地">
                        <Download /> 下载
                      </Button>
                    )}
                    <Button size="sm" variant="ghost" className="flex-1 text-destructive hover:text-destructive" onClick={() => onDelete(a)} title="删除">
                      <Trash2 /> 删除
                    </Button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
