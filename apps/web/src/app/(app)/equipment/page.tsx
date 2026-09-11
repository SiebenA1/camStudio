"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Camera, Save, Wand2 } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import type { CatalogGroup, EquipmentCatalog, EquipmentProfile, EquipmentSpecs } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function EquipmentPage() {
  const qc = useQueryClient();
  const [camera, setCamera] = useState("");
  const [lens, setLens] = useState("");

  const { data: profile } = useQuery({
    queryKey: ["equipment"],
    queryFn: () => api.get<EquipmentProfile>("/admin/equipment"),
  });

  const { data: catalog } = useQuery({
    queryKey: ["equipment-catalog"],
    queryFn: () => api.get<EquipmentCatalog>("/admin/equipment/catalog"),
    staleTime: Infinity,
  });

  useEffect(() => {
    if (profile?.camera_model != null) setCamera(profile.camera_model);
    if (profile?.lens_model != null) setLens(profile.lens_model);
  }, [profile]);

  const saveMutation = useMutation({
    mutationFn: () =>
      api.put<EquipmentProfile>("/admin/equipment", {
        camera_model: camera || null,
        lens_model: lens || null,
      }),
    onSuccess: () => {
      toast.success("已保存");
      qc.invalidateQueries({ queryKey: ["equipment"] });
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "保存失败"),
  });

  const fetchMutation = useMutation({
    mutationFn: () =>
      api.post<EquipmentProfile>("/admin/equipment/fetch-specs", {
        camera_model: camera || null,
        lens_model: lens || null,
      }),
    onSuccess: () => {
      toast.success("官方参数已获取并缓存");
      qc.invalidateQueries({ queryKey: ["equipment"] });
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "获取失败"),
  });

  const canFetch = Boolean(camera || lens);

  return (
    <div className="max-w-3xl">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold">拍摄设备配置</h1>
        <p className="text-sm text-muted-foreground">
          下拉选择你使用的相机与镜头型号，AI 获取一次官方参数并缓存，之后推荐拍摄参数时自动引用（换型号才会重新获取）
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Camera className="h-4 w-4" /> 相机与镜头</CardTitle>
          <CardDescription>从下方下拉框中选择，无需手动输入</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="camera">相机型号</Label>
              <Select id="camera" value={camera} onChange={(e) => setCamera(e.target.value)}>
                <option value="">请选择相机型号</option>
                {(catalog?.cameras ?? []).map((g: CatalogGroup) => (
                  <optgroup key={g.brand} label={g.brand}>
                    {g.models.map((m) => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </optgroup>
                ))}
                {camera && catalog && !catalog.cameras.some((g) => g.models.includes(camera)) && (
                  <option value={camera}>{camera}（当前已保存）</option>
                )}
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="lens">镜头型号</Label>
              <Select id="lens" value={lens} onChange={(e) => setLens(e.target.value)}>
                <option value="">请选择镜头型号</option>
                {(catalog?.lenses ?? []).map((g: CatalogGroup) => (
                  <optgroup key={g.brand} label={g.brand}>
                    {g.models.map((m) => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </optgroup>
                ))}
                {lens && catalog && !catalog.lenses.some((g) => g.models.includes(lens)) && (
                  <option value={lens}>{lens}（当前已保存）</option>
                )}
              </Select>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Button onClick={() => saveMutation.mutate()} disabled={saveMutation.isPending}>
              <Save /> 保存
            </Button>
            <Button variant="outline" onClick={() => fetchMutation.mutate()} disabled={fetchMutation.isPending || !canFetch}>
              <Wand2 /> {fetchMutation.isPending ? "获取中…" : "获取官方参数"}
            </Button>
            {!canFetch && (
              <span className="text-xs text-muted-foreground">请先在上方选择相机或镜头型号</span>
            )}
          </div>
        </CardContent>
      </Card>

      {profile?.specs ? (
        <Card className="mt-4">
          <CardHeader>
            <CardTitle className="text-base">已缓存的官方参数</CardTitle>
          </CardHeader>
          <CardContent>
            <SpecsView specs={profile.specs} />
          </CardContent>
        </Card>
      ) : (
        <p className="mt-4 text-sm text-muted-foreground">
          还没有缓存参数。选择型号后点「获取官方参数」即可（只需获取一次）。
        </p>
      )}
    </div>
  );
}

function SpecsView({ specs }: { specs: EquipmentSpecs }) {
  const cam = specs.camera;
  const lens = specs.lens;
  return (
    <div className="space-y-3 text-sm">
      {cam && (
        <div className="rounded-md border p-3">
          <Badge variant="secondary" className="mb-2">机身</Badge>
          <div className="grid grid-cols-2 gap-1 text-xs text-muted-foreground sm:grid-cols-3">
            {cam.model && <span><b>型号：</b>{cam.model}</span>}
            {cam.sensor && <span><b>传感器：</b>{cam.sensor}</span>}
            {cam.resolution && <span><b>像素：</b>{cam.resolution}</span>}
            {cam.iso_range && <span><b>ISO：</b>{cam.iso_range}</span>}
            {cam.shutter_range && <span><b>快门：</b>{cam.shutter_range}</span>}
            {cam.sync_speed && <span><b>同步速度：</b>{cam.sync_speed}</span>}
          </div>
        </div>
      )}
      {lens && (
        <div className="rounded-md border p-3">
          <Badge variant="secondary" className="mb-2">镜头</Badge>
          <div className="grid grid-cols-2 gap-1 text-xs text-muted-foreground sm:grid-cols-3">
            {lens.model && <span><b>型号：</b>{lens.model}</span>}
            {lens.focal_range && <span><b>焦段：</b>{lens.focal_range}</span>}
            {lens.max_aperture && <span><b>最大光圈：</b>{lens.max_aperture}</span>}
            {lens.stabilization && <span><b>防抖：</b>{lens.stabilization}</span>}
          </div>
        </div>
      )}
      {specs.note && <p className="text-xs text-amber-600">⚠ {specs.note}</p>}
    </div>
  );
}
