"use client";

import { useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Camera, ImagePlus, RefreshCw, ScanSearch, Sparkles, Trash2, Upload } from "lucide-react";
import { toast } from "sonner";
import { api, assetUrl } from "@/lib/api";
import type { Guidance, ReferenceShot, SceneAnalysis } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export function ReferenceShotPanel({ projectId }: { projectId: string }) {
  const qc = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  // replaceTarget：null=新上传；string=替换该空镜图。共用一个文件选择框。
  const [replaceTarget, setReplaceTarget] = useState<string | null>(null);

  const { data: shots } = useQuery({
    queryKey: ["reference-shots", projectId],
    queryFn: () => api.get<ReferenceShot[]>(`/projects/${projectId}/reference-shots`),
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => api.postFile<ReferenceShot>(`/projects/${projectId}/reference-shots`, file),
    onSuccess: () => {
      toast.success("空镜图已上传");
      qc.invalidateQueries({ queryKey: ["reference-shots", projectId] });
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "上传失败"),
  });

  const replaceMutation = useMutation({
    mutationFn: ({ id, file }: { id: string; file: File }) => api.postFile<ReferenceShot>(`/reference-shots/${id}/replace`, file),
    onSuccess: () => {
      toast.success("空镜图已更换（分析/指导已重置）");
      qc.invalidateQueries({ queryKey: ["reference-shots", projectId] });
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "更换失败"),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.del(`/reference-shots/${id}`),
    onSuccess: () => {
      toast.success("空镜图已删除");
      qc.invalidateQueries({ queryKey: ["reference-shots", projectId] });
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "删除失败"),
  });

  const analyzeMutation = useMutation({
    mutationFn: (id: string) => api.post<SceneAnalysis>(`/reference-shots/${id}/analyze`, {}),
    onSuccess: () => {
      toast.success("场景分析完成");
      qc.invalidateQueries({ queryKey: ["reference-shots", projectId] });
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "分析失败"),
  });

  const guidanceMutation = useMutation({
    mutationFn: (id: string) => api.post<Guidance>(`/reference-shots/${id}/guidance`, {}),
    onSuccess: () => {
      toast.success("拍摄指导已生成");
      qc.invalidateQueries({ queryKey: ["reference-shots", projectId] });
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "指导生成失败"),
  });

  const generateMutation = useMutation({
    mutationFn: (id: string) => api.post<{ asset_ids: string[] }>(`/reference-shots/${id}/generate`, {}),
    onSuccess: (r) => {
      toast.success(`已提交 ${r.asset_ids?.length ?? 3} 张素描草图任务，稍后刷新预演资产查看`);
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
            <Camera className="h-4 w-4" /> 空镜图生预演
          </CardTitle>
          <CardDescription>
            上传实拍空镜图，AI 分析场景并生成拍摄指导，再输出 3 张不同姿势的手绘素描草图（单色线稿）
          </CardDescription>
        </div>
        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={onFileChange}
        />
        <Button variant="outline" onClick={() => openUpload(null)} disabled={uploadMutation.isPending}>
          <Upload /> {shots?.length ? "再传一张" : "上传空镜图"}
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        {shots && shots.length > 0 ? (
          <div className="space-y-4">
            {shots.map((s) => (
              <div key={s.id} className="grid grid-cols-1 gap-4 rounded-md border p-4 lg:grid-cols-[240px_1fr]">
                <div>
                  <div className="aspect-square overflow-hidden rounded-md bg-muted">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={assetUrl(s.file_url)} alt="空镜图" className="h-full w-full object-cover" />
                  </div>
                  <div className="mt-2 grid grid-cols-2 gap-1.5">
                    <Button size="sm" variant="outline" onClick={() => analyzeMutation.mutate(s.id)} disabled={analyzeMutation.isPending}>
                      <ScanSearch /> 分析场景
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => guidanceMutation.mutate(s.id)} disabled={guidanceMutation.isPending || !s.analysis_json}>
                      <Sparkles /> 生成指导
                    </Button>
                    <Button size="sm" onClick={() => generateMutation.mutate(s.id)} disabled={generateMutation.isPending}>
                      <ImagePlus /> 生成素描草图 ×3
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => openUpload(s.id)} disabled={replaceMutation.isPending}>
                      <RefreshCw /> 更换
                    </Button>
                    <Button size="sm" variant="outline" className="col-span-2 text-destructive hover:text-destructive" onClick={() => {
                      if (window.confirm("确定删除这张空镜图吗？")) deleteMutation.mutate(s.id);
                    }}>
                      <Trash2 /> 删除空镜图
                    </Button>
                  </div>
                </div>

                <div className="space-y-3 text-sm">
                  {s.analysis_json ? (
                    <SceneAnalysisView a={s.analysis_json} />
                  ) : (
                    <p className="text-muted-foreground">尚未分析。点击「分析场景」识别光线/机位/构图/色彩等。</p>
                  )}
                  {s.guidance_json && <GuidanceView g={s.guidance_json} />}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-12 text-center">
            <Camera className="mb-3 h-10 w-10 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">还没有空镜图，上传一张实拍空镜图开始图生预演</p>
            <Button variant="outline" className="mt-4" onClick={() => openUpload(null)}>
              <Upload /> 上传空镜图
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function SceneAnalysisView({ a }: { a: SceneAnalysis }) {
  const lighting = a.lighting;
  const camera = a.camera;
  const composition = a.composition;
  const color = a.color;
  return (
    <div className="rounded-md bg-muted/50 p-3">
      <div className="mb-2 flex items-center gap-2">
        <Badge variant="secondary">场景分析</Badge>
        {a.scene_type && <span className="font-medium">{a.scene_type}</span>}
      </div>
      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-muted-foreground">
        {lighting && (
          <span>光线：{lighting.direction ?? "-"} / {lighting.temperature ?? "-"} / {lighting.intensity ?? "-"}</span>
        )}
        {camera && (
          <span>机位：{camera.angle ?? "-"} · {camera.lens_suggestion ?? "-"}</span>
        )}
        {composition && <span>构图：{composition.rule ?? "-"}</span>}
        {color?.mood && <span>色彩：{color.mood}</span>}
        {a.space?.subject_zone && <span className="col-span-2">主体区域：{a.space.subject_zone}</span>}
        {a.challenge && <span className="col-span-2">注意：{a.challenge}</span>}
      </div>
    </div>
  );
}

function GuidanceView({ g }: { g: Guidance }) {
  const el = g.elements;
  return (
    <div className="space-y-3">
      <div className="rounded-md bg-accent/40 p-3">
        <div className="mb-2 flex items-center gap-2">
          <Badge variant="default">拍摄指导</Badge>
          <span className="text-xs text-muted-foreground">拍摄位置 / 角度 / 姿势 / 表情 / 构图由工具推导</span>
        </div>
        {g.camera_plan && (
          <div className="mb-2 rounded-md bg-primary/10 p-2 text-xs">
            {g.camera_plan.subject_position && <div className="mb-0.5"><b>主体拍摄位置：</b>{g.camera_plan.subject_position}</div>}
            {g.camera_plan.camera_angle && <div className="mb-0.5"><b>机位角度：</b>{g.camera_plan.camera_angle}</div>}
            {g.camera_plan.shooting_position && <div><b>相机位置/方向：</b>{g.camera_plan.shooting_position}</div>}
          </div>
        )}
        {g.shot_list && g.shot_list.length > 0 && (
          <div className="space-y-1.5">
            {g.shot_list.map((s, i) => (
              <div key={i} className="text-xs">
                <span className="font-medium">{s.shot ?? `镜头 ${i + 1}`}</span>
                <span className="text-muted-foreground"> · {s.camera ?? ""}{s.subject ? ` · ${s.subject}` : ""}</span>
                {s.note && <div className="text-muted-foreground">　{s.note}</div>}
              </div>
            ))}
          </div>
        )}
      </div>
      {el && (
        <div className="grid grid-cols-1 gap-1 text-xs text-muted-foreground sm:grid-cols-2">
          {el.character && <span><b>人物：</b>{el.character}</span>}
          {el.outfit && <span><b>服装：</b>{el.outfit}</span>}
          {el.pose && <span><b>姿势（工具推导）：</b>{el.pose}</span>}
          {el.expression && <span><b>表情（工具推导）：</b>{el.expression}</span>}
          {el.composition && <span className="sm:col-span-2"><b>构图（工具推导）：</b>{el.composition}</span>}
        </div>
      )}
      {g.lighting_setup && <p className="text-xs text-muted-foreground"><b>灯光：</b>{g.lighting_setup}</p>}
      {g.props_needed && g.props_needed.length > 0 && (
        <p className="text-xs text-muted-foreground"><b>道具：</b>{g.props_needed.join("、")}</p>
      )}
      {g.risk_tips && g.risk_tips.length > 0 && (
        <div className="text-xs text-amber-600">
          {g.risk_tips.map((t, i) => <div key={i}>⚠ {t}</div>)}
        </div>
      )}
    </div>
  );
}
