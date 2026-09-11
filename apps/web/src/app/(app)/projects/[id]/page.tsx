"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { Project } from "@/lib/types";
import { ReferenceShotPanel } from "@/components/projects/reference-shot-panel";
import { AssetGallery } from "@/components/previz/asset-gallery";

const STATUS_LABELS: Record<string, string> = {
  draft: "草稿",
  briefing: "需求阶段",
  previz: "预演中",
  reviewing: "评审中",
  locked: "已锁定",
  shooting: "实拍中",
  post: "后期中",
  delivering: "交付中",
  delivered: "已交付",
  archived: "已归档",
};

export default function ProjectDetailPage() {
  const params = useParams<{ id: string }>();
  const projectId = params.id;

  const { data: project } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => api.get<Project>(`/projects/${projectId}`),
  });

  return (
    <div className="space-y-6">
      <div>
        <Link href="/projects" className="mb-3 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" /> 返回项目列表
        </Link>
        <div>
          <h1 className="text-2xl font-semibold">{project?.name ?? "项目"}</h1>
          <p className="text-sm text-muted-foreground">
            {project?.brand ? `${project.brand} · ` : ""}状态：
            {project?.status ? (STATUS_LABELS[project.status] ?? project.status) : "-"}
          </p>
        </div>
      </div>

      {/* 核心流程：上传模特照片 → AI 自动分析 → 预演草图 + 推荐相机参数 */}
      <ReferenceShotPanel projectId={projectId} />

      <div>
        <h2 className="mb-3 text-lg font-semibold">预演资产</h2>
        <AssetGallery projectId={projectId} />
      </div>
    </div>
  );
}
