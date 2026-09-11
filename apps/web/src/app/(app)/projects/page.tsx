"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Download, FolderKanban, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { api, saveBlob } from "@/lib/api";
import type { Project } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { formatDateTime } from "@/lib/utils";

const STATUS_META: Record<string, { label: string; variant: "secondary" | "default" | "warning" | "success" | "outline" }> = {
  draft: { label: "草稿", variant: "secondary" },
  briefing: { label: "Brief 阶段", variant: "secondary" },
  previz: { label: "预演中", variant: "default" },
  reviewing: { label: "评审中", variant: "warning" },
  locked: { label: "已锁定", variant: "success" },
  shooting: { label: "实拍中", variant: "warning" },
  post: { label: "后期中", variant: "warning" },
  delivering: { label: "交付中", variant: "default" },
  delivered: { label: "已交付", variant: "success" },
  archived: { label: "已归档", variant: "outline" },
};

export default function ProjectsPage() {
  const router = useRouter();
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [exportingId, setExportingId] = useState<string | null>(null);

  const { data: projects, isLoading } = useQuery({
    queryKey: ["projects"],
    queryFn: () => api.get<Project[]>("/projects"),
  });

  const createMutation = useMutation({
    mutationFn: (body: Partial<Project>) => api.post<Project>("/projects", body),
    onSuccess: (p) => {
      qc.invalidateQueries({ queryKey: ["projects"] });
      setOpen(false);
      toast.success("项目已创建");
      router.push(`/projects/${p.id}`);
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "创建失败"),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.del(`/projects/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["projects"] });
      toast.success("项目已删除");
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "删除失败"),
  });

  function onDelete(p: Project) {
    if (window.confirm(`确定删除项目「${p.name}」吗？\n（项目及其空镜图、预演资产、评审将不再显示）`)) {
      deleteMutation.mutate(p.id);
    }
  }

  async function onExport(p: Project) {
    setExportingId(p.id);
    toast.loading("正在打包导出…", { id: "export" });
    try {
      const { blob, filename } = await api.download(`/projects/${p.id}/export`);
      saveBlob(blob, filename);
      toast.success("导出完成", { id: "export" });
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "导出失败", { id: "export" });
    } finally {
      setExportingId(null);
    }
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">项目中心</h1>
          <p className="text-sm text-muted-foreground">管理与跟踪你的商业摄影项目</p>
        </div>
        <Button onClick={() => setOpen(true)}>
          <Plus /> 新建项目
        </Button>
      </div>

      {isLoading ? (
        <div className="text-muted-foreground">加载中…</div>
      ) : !projects?.length ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-16 text-center">
            <FolderKanban className="mb-3 h-10 w-10 text-muted-foreground" />
            <p className="text-muted-foreground">还没有项目，点击「新建项目」开始</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((p) => {
            const meta = STATUS_META[p.status] ?? { label: p.status, variant: "outline" as const };
            return (
              <Card
                key={p.id}
                className="flex cursor-pointer flex-col transition-shadow hover:shadow-md"
                onClick={() => router.push(`/projects/${p.id}`)}
              >
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <CardTitle className="line-clamp-1">{p.name}</CardTitle>
                    <Badge variant={meta.variant}>{meta.label}</Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">{p.brand || "未设置品牌"}</p>
                </CardHeader>
                <CardContent className="flex flex-1 flex-col justify-between">
                  <div>
                    <p className="line-clamp-2 text-sm text-muted-foreground">{p.description || "暂无描述"}</p>
                    <p className="mt-3 text-xs text-muted-foreground">
                      更新于 {formatDateTime(p.updated_at)}
                    </p>
                  </div>
                  <div className="mt-3 flex gap-1 border-t pt-3">
                    <Button
                      size="sm"
                      variant="ghost"
                      className="flex-1"
                      disabled={exportingId === p.id}
                      onClick={(e) => {
                        e.stopPropagation();
                        onExport(p);
                      }}
                    >
                      <Download /> {exportingId === p.id ? "导出中…" : "导出"}
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="flex-1 text-destructive hover:text-destructive"
                      onClick={(e) => {
                        e.stopPropagation();
                        onDelete(p);
                      }}
                    >
                      <Trash2 /> 删除
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      <CreateProjectDialog
        open={open}
        onClose={() => setOpen(false)}
        onSubmit={(body) => createMutation.mutate(body)}
        loading={createMutation.isPending}
      />
    </div>
  );
}

function CreateProjectDialog({
  open,
  onClose,
  onSubmit,
  loading,
}: {
  open: boolean;
  onClose: () => void;
  onSubmit: (body: Partial<Project>) => void;
  loading: boolean;
}) {
  const [name, setName] = useState("");
  const [brand, setBrand] = useState("");
  const [description, setDescription] = useState("");
  const [budget, setBudget] = useState("");

  return (
    <Dialog open={open} onClose={onClose} title="新建项目">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit({ name, brand: brand || null, description: description || null, budget: budget ? Number(budget) : null });
        }}
        className="space-y-4"
      >
        <div className="space-y-2">
          <Label htmlFor="name">项目名称 *</Label>
          <Input id="name" value={name} onChange={(e) => setName(e.target.value)} required placeholder="例如：春季新品系列大片" />
        </div>
        <div className="space-y-2">
          <Label htmlFor="brand">品牌</Label>
          <Input id="brand" value={brand} onChange={(e) => setBrand(e.target.value)} placeholder="品牌名" />
        </div>
        <div className="space-y-2">
          <Label htmlFor="desc">描述</Label>
          <Textarea id="desc" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="项目背景与目标" />
        </div>
        <div className="space-y-2">
          <Label htmlFor="budget">预算（元）</Label>
          <Input id="budget" type="number" value={budget} onChange={(e) => setBudget(e.target.value)} placeholder="可选" />
        </div>
        <div className="flex justify-end gap-2">
          <Button type="button" variant="outline" onClick={onClose}>取消</Button>
          <Button type="submit" disabled={loading}>{loading ? "创建中…" : "创建"}</Button>
        </div>
      </form>
    </Dialog>
  );
}
