"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, ImagePlus } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";
import { api } from "@/lib/api";
import type { Project } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { BriefPanel } from "@/components/projects/brief-panel";
import { ReferenceShotPanel } from "@/components/projects/reference-shot-panel";
import { AssetGallery } from "@/components/previz/asset-gallery";

const SIZES = ["1024*1024", "1024*1536", "1536*1024", "2048*2048"];

export default function ProjectDetailPage() {
  const params = useParams<{ id: string }>();
  const projectId = params.id;
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);

  const { data: project } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => api.get<Project>(`/projects/${projectId}`),
  });

  const generateMutation = useMutation({
    mutationFn: (body: { count: number; size: string }) => {
      const [w, h] = body.size.split("*").map(Number);
      return api.post(`/projects/${projectId}/previz/generate`, {
        count: body.count,
        width: w,
        height: h,
      });
    },
    onSuccess: () => {
      setOpen(false);
      toast.success("已提交生成任务，稍后刷新查看");
      qc.invalidateQueries({ queryKey: ["previz", projectId] });
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "提交失败"),
  });

  return (
    <div className="space-y-6">
      <div>
        <Link href="/projects" className="mb-3 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" /> 返回项目列表
        </Link>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">{project?.name ?? "项目"}</h1>
            <p className="text-sm text-muted-foreground">
              {project?.brand ? `${project.brand} · ` : ""}状态：{project?.status}
            </p>
          </div>
          <Button onClick={() => setOpen(true)}>
            <ImagePlus /> 生成预演
          </Button>
        </div>
      </div>

      <BriefPanel projectId={projectId} />

      <ReferenceShotPanel projectId={projectId} />

      <div>
        <h2 className="mb-3 text-lg font-semibold">预演资产</h2>
        <AssetGallery projectId={projectId} />
      </div>

      <GenerateDialog
        open={open}
        onClose={() => setOpen(false)}
        onSubmit={(body) => generateMutation.mutate(body)}
        loading={generateMutation.isPending}
      />
    </div>
  );
}

function GenerateDialog({
  open,
  onClose,
  onSubmit,
  loading,
}: {
  open: boolean;
  onClose: () => void;
  onSubmit: (body: { count: number; size: string }) => void;
  loading: boolean;
}) {
  const [count, setCount] = useState(2);
  const [size, setSize] = useState("1024*1024");

  return (
    <Dialog open={open} onClose={onClose} title="生成预演" description="基于当前选中的变量组合批量生成视觉方案">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit({ count, size });
        }}
        className="space-y-4"
      >
        <div className="space-y-2">
          <Label>生成张数</Label>
          <Input type="number" min={1} max={8} value={count} onChange={(e) => setCount(Number(e.target.value))} />
        </div>
        <div className="space-y-2">
          <Label>尺寸</Label>
          <div className="flex flex-wrap gap-2">
            {SIZES.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => setSize(s)}
                className={`rounded-md border px-3 py-1.5 text-sm ${
                  size === s ? "border-primary bg-accent text-accent-foreground" : "hover:bg-accent"
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
        <p className="text-xs text-muted-foreground">
          使用默认文生图模型（可在「模型配置」中切换）。生成后可在资产上做质量评分与评审。
        </p>
        <div className="flex justify-end gap-2">
          <Button type="button" variant="outline" onClick={onClose}>取消</Button>
          <Button type="submit" disabled={loading}>{loading ? "提交中…" : "开始生成"}</Button>
        </div>
      </form>
    </Dialog>
  );
}
