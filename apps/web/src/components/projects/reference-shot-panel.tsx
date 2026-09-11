"use client";

import { useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Camera, ImagePlus, RefreshCw, ScanSearch, Sparkles, Trash2, Upload } from "lucide-react";
import { toast } from "sonner";
import { api, assetUrl } from "@/lib/api";
import type { CameraParams, PhotoAnalysis, PoseStyle, ReferenceShot } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const RENDER_LEVELS = [
  { value: "outline", label: "轮廓" },
  { value: "simple", label: "简笔" },
  { value: "detailed", label: "精细" },
] as const;

export function ReferenceShotPanel({ projectId }: { projectId: string }) {
  const qc = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [replaceTarget, setReplaceTarget] = useState<string | null>(null);
  const [selectedStyle, setSelectedStyle] = useState<string | null>(null);
  const [count, setCount] = useState(3);
  const [renderLevel, setRenderLevel] = useState<string>("detailed");

  const { data: shots } = useQuery({
    queryKey: ["reference-shots", projectId],
    queryFn: () => api.get<ReferenceShot[]>(`/projects/${projectId}/reference-shots`),
  });

  const { data: styles } = useQuery({
    queryKey: ["pose-styles"],
    queryFn: () => api.get<PoseStyle[]>("/reference-shots/styles"),
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => api.postFile<ReferenceShot>(`/projects/${projectId}/reference-shots`, file),
    onSuccess: () => {
      toast.success("模特照片已上传");
      qc.invalidateQueries({ queryKey: ["reference-shots", projectId] });
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "上传失败"),
  });

  const replaceMutation = useMutation({
    mutationFn: ({ id, file }: { id: string; file: File }) => api.postFile<ReferenceShot>(`/reference-shots/${id}/replace`, file),
    onSuccess: () => {
      toast.success("照片已更换（分析/建议已重置）");
      qc.invalidateQueries({ queryKey: ["reference-shots", projectId] });
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "更换失败"),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.del(`/reference-shots/${id}`),
    onSuccess: () => {
      toast.success("照片已删除");
      qc.invalidateQueries({ queryKey: ["reference-shots", projectId] });
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "删除失败"),
  });

  const analyzeMutation = useMutation({
    mutationFn: (id: string) => api.post<PhotoAnalysis>(`/reference-shots/${id}/analyze`, {}),
    onSuccess: () => {
      toast.success("照片分析完成");
      qc.invalidateQueries({ queryKey: ["reference-shots", projectId] });
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "分析失败"),
  });

  const recommendMutation = useMutation({
    mutationFn: (id: string) => api.post<{ camera_params?: CameraParams }>(`/reference-shots/${id}/recommend`, {}),
    onSuccess: () => {
      toast.success("拍摄建议已生成");
      qc.invalidateQueries({ queryKey: ["reference-shots", projectId] });
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "建议生成失败"),
  });

  const generateMutation = useMutation({
    mutationFn: ({ id, styleId, count, renderLevel }: { id: string; styleId: string | null; count: number; renderLevel: string }) =>
      api.post<{ asset_ids: string[] }>(`/reference-shots/${id}/generate`, { style_id: styleId, count, render_level: renderLevel }),
    onSuccess: (r) => {
      toast.success(`已提交 ${r.asset_ids?.length ?? count} 张预演草图任务，稍后刷新预演资产查看`);
      qc.invalidateQueries({ queryKey: ["previz", projectId] });
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "生成失败"),
  });

  function openUpload(replaceId: string | null) {
    setReplaceTarget(replaceId);
    fileRef.current?.click();
  }

  function onFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (f) {
      if (replaceTarget) replaceMutation.mutate({ id: replaceTarget, file: f });
      else uploadMutation.mutate(f);
    }
    e.target.value = "";
    setReplaceTarget(null);
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between">
        <div>
          <CardTitle className="flex items-center gap-2">
            <Camera className="h-4 w-4" /> 模特照片预演
          </CardTitle>
          <CardDescription>
            上传一张带模特的实拍照片，AI 自动分析并生成卡通形象预演草图（不复刻真人脸）+ 推荐相机参数
          </CardDescription>
        </div>
        <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={onFileChange} />
        <Button variant="outline" onClick={() => openUpload(null)} disabled={uploadMutation.isPending}>
          <Upload /> {shots?.length ? "再传一张" : "上传模特照片"}
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        {styles && styles.length > 0 && (
          <div>
            <div className="mb-2 text-sm font-medium text-muted-foreground">
              姿势风格（可选，点选后按该风格生成草图）
            </div>
            <div className="flex flex-wrap gap-1.5">
              <button
                onClick={() => setSelectedStyle(null)}
                className={cn(
                  "rounded-full border px-3 py-1 text-xs transition-colors",
                  selectedStyle === null
                    ? "border-primary bg-primary text-primary-foreground"
                    : "bg-muted text-muted-foreground hover:bg-accent"
                )}
              >
                ✨ 自动（AI 推荐）
              </button>
              {styles.map((s) => (
                <button
                  key={s.id}
                  title={s.hint}
                  onClick={() => setSelectedStyle(s.id)}
                  className={cn(
                    "rounded-full border px-3 py-1 text-xs transition-colors",
                    selectedStyle === s.id
                      ? "border-primary bg-primary text-primary-foreground"
                      : "bg-muted text-muted-foreground hover:bg-accent"
                  )}
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-muted-foreground">张数</span>
            {[1, 2, 3, 4, 5, 6].map((n) => (
              <button
                key={n}
                onClick={() => setCount(n)}
                className={cn(
                  "rounded-md border px-2.5 py-1 text-xs transition-colors",
                  count === n ? "border-primary bg-primary text-primary-foreground" : "bg-muted text-muted-foreground hover:bg-accent"
                )}
              >
                {n}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-muted-foreground">渲染</span>
            {RENDER_LEVELS.map((l) => (
              <button
                key={l.value}
                onClick={() => setRenderLevel(l.value)}
                className={cn(
                  "rounded-md border px-2.5 py-1 text-xs transition-colors",
                  renderLevel === l.value ? "border-primary bg-primary text-primary-foreground" : "bg-muted text-muted-foreground hover:bg-accent"
                )}
              >
                {l.label}
              </button>
            ))}
          </div>
        </div>

        {shots && shots.length > 0 ? (
          <div className="space-y-4">
            {shots.map((s) => (
              <div key={s.id} className="grid grid-cols-1 gap-4 rounded-md border p-4 lg:grid-cols-[240px_1fr]">
                <div>
                  <div className="aspect-square overflow-hidden rounded-md bg-muted">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={assetUrl(s.file_url)} alt="模特照片" className="h-full w-full object-cover" />
                  </div>
                  <div className="mt-2 grid grid-cols-2 gap-1.5">
                    <Button size="sm" variant="outline" onClick={() => analyzeMutation.mutate(s.id)} disabled={analyzeMutation.isPending}>
                      <ScanSearch /> 分析照片
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => recommendMutation.mutate(s.id)} disabled={recommendMutation.isPending || !s.analysis_json}>
                      <Sparkles /> 生成建议
                    </Button>
                    <Button size="sm" onClick={() => generateMutation.mutate({ id: s.id, styleId: selectedStyle, count, renderLevel })} disabled={generateMutation.isPending}>
                      <ImagePlus /> 生成草图 ×{count}
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => openUpload(s.id)} disabled={replaceMutation.isPending}>
                      <RefreshCw /> 更换
                    </Button>
                    <Button size="sm" variant="outline" className="col-span-2 text-destructive hover:text-destructive" onClick={() => {
                      if (window.confirm("确定删除这张照片吗？")) deleteMutation.mutate(s.id);
                    }}>
                      <Trash2 /> 删除照片
                    </Button>
                  </div>
                </div>

                <div className="space-y-3 text-sm">
                  {s.analysis_json ? (
                    <PhotoAnalysisView a={s.analysis_json} />
                  ) : (
                    <p className="text-muted-foreground">点击「分析照片」自动识别场景/光线/人像/穿着/道具等元素。</p>
                  )}
                  {s.guidance_json?.camera_params && <CameraParamsView p={s.guidance_json.camera_params} />}
                  {s.guidance_json?.elements && <RecommendView g={s.guidance_json} />}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-12 text-center">
            <Camera className="mb-3 h-10 w-10 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">上传一张带模特的实拍照片，AI 自动完成预演分析</p>
            <Button variant="outline" className="mt-4" onClick={() => openUpload(null)}>
              <Upload /> 上传模特照片
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function PhotoAnalysisView({ a }: { a: PhotoAnalysis }) {
  const lighting = a.lighting;
  const model = a.model;
  const outfit = a.outfit;
  const composition = a.composition;
  return (
    <div className="rounded-md bg-muted/50 p-3">
      <div className="mb-2 flex items-center gap-2">
        <Badge variant="secondary">照片分析</Badge>
        {a.scene?.type && <span className="font-medium">{a.scene.type}</span>}
      </div>
      <div className="grid grid-cols-1 gap-1 text-xs text-muted-foreground sm:grid-cols-2">
        {a.scene?.background && <span className="sm:col-span-2"><b>背景：</b>{a.scene.background}</span>}
        {lighting && <span><b>光线：</b>{lighting.direction ?? "-"} / {lighting.temperature ?? "-"} / {lighting.intensity ?? "-"}</span>}
        {model && <span><b>模特：</b>{[model.gender, model.age, model.style].filter(Boolean).join(" · ") || "-"}</span>}
        {outfit?.clothing && <span className="sm:col-span-2"><b>穿着：</b>{outfit.clothing}{outfit.colors?.length ? `（${outfit.colors.join("、")}）` : ""}</span>}
        {composition && <span><b>构图：</b>{composition.rule ?? "-"} · {composition.angle ?? "-"}</span>}
        {a.props?.length ? <span><b>道具：</b>{a.props.join("、")}</span> : null}
        {a.improvement?.length ? (
          <span className="sm:col-span-2 text-amber-600"><b>可优化：</b>{a.improvement.join("；")}</span>
        ) : null}
      </div>
    </div>
  );
}

/** 把参数值拆成「主参数」与「补充说明」：以分号为界，主参数加粗突出 */
function splitPrimary(value: string): [string, string] {
  const i = value.search(/[；;]/);
  if (i > 0) return [value.slice(0, i).trim(), value.slice(i + 1).trim()];
  return [value, ""];
}

function CameraParamsView({ p }: { p: CameraParams }) {
  const rows = ([
    ["光圈", p.aperture],
    ["快门", p.shutter_speed],
    ["ISO", p.iso],
    ["焦段", p.focal_length],
    ["白平衡", p.white_balance],
    ["驱动", p.drive_mode],
  ] as [string, string | undefined][]).filter((row): row is [string, string] => Boolean(row[1]));

  return (
    <div className="overflow-hidden rounded-md border border-primary/30">
      <div className="border-b border-primary/20 bg-primary/10 px-3 py-1.5">
        <span className="text-xs font-semibold text-primary">推荐相机参数</span>
      </div>
      <div className="divide-y divide-border">
        {rows.map(([label, value]) => {
          const [main, rest] = splitPrimary(value);
          return (
            <div key={label} className="flex gap-3 px-3 py-2">
              <span className="w-12 shrink-0 pt-0.5 text-xs font-semibold text-primary">{label}</span>
              <div className="min-w-0 flex-1">
                <div className="text-sm font-medium leading-snug">{main}</div>
                {rest && <div className="mt-0.5 text-xs leading-snug text-muted-foreground">{rest}</div>}
              </div>
            </div>
          );
        })}
      </div>
      {p.note && (
        <div className="border-t border-border bg-muted/40 px-3 py-2 text-xs leading-snug text-muted-foreground">
          {p.note}
        </div>
      )}
    </div>
  );
}

function RecommendView({ g }: { g: { elements?: { pose?: string; expression?: string; composition?: string }; risk_tips?: string[] } }) {
  const el = g.elements ?? {};
  return (
    <div className="space-y-2 text-xs text-muted-foreground">
      {el.pose && <div><b>姿势：</b>{el.pose}</div>}
      {el.expression && <div><b>表情：</b>{el.expression}</div>}
      {el.composition && <div><b>构图：</b>{el.composition}</div>}
      {g.risk_tips?.length ? (
        <div className="text-amber-600">{g.risk_tips.map((t, i) => <div key={i}>⚠ {t}</div>)}</div>
      ) : null}
    </div>
  );
}
