"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Pencil, Plus, Power, Star, Trash2, Zap } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { TASK_TYPE_LABELS, type ModelConfig } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface ProviderInfo {
  provider: string;
  label: string;
  task_types: string[];
  description: string;
  example_base_url: string;
}

interface FormState {
  id?: string;
  provider: string;
  name: string;
  base_url: string;
  api_key: string;
  model: string;
  task_type: string;
  is_default: boolean;
  enabled: boolean;
}

const EMPTY: FormState = {
  provider: "openai_compat",
  name: "",
  base_url: "",
  api_key: "",
  model: "",
  task_type: "chat",
  is_default: false,
  enabled: true,
};

export default function ModelsPage() {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<FormState>(EMPTY);

  const { data: models } = useQuery({
    queryKey: ["models"],
    queryFn: () => api.get<ModelConfig[]>("/admin/models"),
  });
  const { data: providers } = useQuery({
    queryKey: ["providers"],
    queryFn: () => api.get<ProviderInfo[]>("/admin/models/providers"),
  });

  const saveMutation = useMutation({
    mutationFn: (f: FormState) => {
      const body = { ...f };
      if (!body.api_key) delete (body as Partial<FormState>).api_key;
      return f.id
        ? api.patch<ModelConfig>(`/admin/models/${f.id}`, body)
        : api.post<ModelConfig>("/admin/models", body);
    },
    onSuccess: () => {
      setOpen(false);
      toast.success("已保存");
      qc.invalidateQueries({ queryKey: ["models"] });
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "保存失败"),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.del(`/admin/models/${id}`),
    onSuccess: () => {
      toast.success("已删除");
      qc.invalidateQueries({ queryKey: ["models"] });
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "删除失败"),
  });

  const testMutation = useMutation({
    mutationFn: (id: string) => api.post<{ ok: boolean; message: string; latency_ms?: number }>(`/admin/models/${id}/test`, {}),
    onSuccess: (r) => (r.ok ? toast.success(r.message) : toast.warning(r.message)),
    onError: (e) => toast.error(e instanceof Error ? e.message : "测试失败"),
  });

  const defaultMutation = useMutation({
    mutationFn: (m: ModelConfig) => api.patch(`/admin/models/${m.id}`, { is_default: true }),
    onSuccess: () => {
      toast.success("已设为默认");
      qc.invalidateQueries({ queryKey: ["models"] });
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "设置失败"),
  });

  function openCreate() {
    setForm({ ...EMPTY, provider: providers?.[0]?.provider ?? "openai_compat" });
    setOpen(true);
  }
  function openEdit(m: ModelConfig) {
    setForm({
      id: m.id,
      provider: m.provider,
      name: m.name,
      base_url: m.base_url,
      api_key: "",
      model: m.model,
      task_type: m.task_type,
      is_default: m.is_default,
      enabled: m.enabled,
    });
    setOpen(true);
  }

  const grouped = (models ?? []).reduce<Record<string, ModelConfig[]>>((acc, m) => {
    (acc[m.task_type] ??= []).push(m);
    return acc;
  }, {});

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">模型配置</h1>
          <p className="text-sm text-muted-foreground">
            配置国内大模型接入（DeepSeek、通义千问、智谱、万相等）。最少只需配置「文本（多模态，兼做视觉）」+「文生图」两个即可跑通核心流程；向量为可选（资产库检索用）。
          </p>
        </div>
        <Button onClick={openCreate}>
          <Plus /> 新增模型
        </Button>
      </div>

      <div className="space-y-6">
        {Object.entries(grouped).map(([taskType, list]) => (
          <Card key={taskType}>
            <CardHeader>
              <CardTitle className="text-base">{TASK_TYPE_LABELS[taskType] ?? taskType}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {list.map((m) => (
                <div key={m.id} className={cn("flex items-center justify-between rounded-md border p-3", !m.enabled && "opacity-60")}>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{m.name}</span>
                      {m.is_default && (
                        <Badge variant="default" className="gap-1"><Star className="h-3 w-3" /> 默认</Badge>
                      )}
                      {!m.enabled && <Badge variant="secondary">已停用</Badge>}
                    </div>
                    <p className="truncate text-xs text-muted-foreground">
                      {providers?.find((p) => p.provider === m.provider)?.label ?? m.provider} · {m.model} · {m.base_url}
                    </p>
                    <p className="text-xs text-muted-foreground">密钥：{m.api_key_masked || "未设置"}</p>
                  </div>
                  <div className="flex items-center gap-1">
                    <Button size="sm" variant="outline" onClick={() => testMutation.mutate(m.id)} disabled={testMutation.isPending}>
                      <Zap /> 测试
                    </Button>
                    {!m.is_default && (
                      <Button size="sm" variant="ghost" onClick={() => defaultMutation.mutate(m)} title="设为默认">
                        <Star />
                      </Button>
                    )}
                    <Button size="sm" variant="ghost" onClick={() => openEdit(m)}>
                      <Pencil />
                    </Button>
                    <Button size="sm" variant="ghost" onClick={() => deleteMutation.mutate(m.id)} className="text-destructive">
                      <Trash2 />
                    </Button>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        ))}
        {!models?.length && (
          <Card className="border-dashed">
            <CardContent className="py-12 text-center text-muted-foreground">
              暂无模型配置，点击「新增模型」添加
            </CardContent>
          </Card>
        )}
      </div>

      <Dialog open={open} onClose={() => setOpen(false)} title={form.id ? "编辑模型" : "新增模型"}>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            saveMutation.mutate(form);
          }}
          className="space-y-4"
        >
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label>服务商</Label>
              <Select value={form.provider} onChange={(e) => setForm({ ...form, provider: e.target.value })}>
                {(providers ?? []).map((p) => (
                  <option key={p.provider} value={p.provider}>{p.label}</option>
                ))}
              </Select>
            </div>
            <div className="space-y-2">
              <Label>任务类型</Label>
              <Select value={form.task_type} onChange={(e) => setForm({ ...form, task_type: e.target.value })}>
                {Object.entries(TASK_TYPE_LABELS).map(([k, v]) => (
                  <option key={k} value={k}>{v}</option>
                ))}
              </Select>
            </div>
          </div>
          <div className="space-y-2">
            <Label>名称</Label>
            <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="例如：DeepSeek 文本" required />
          </div>
          <div className="space-y-2">
            <Label>接口地址（Base URL）</Label>
            <Input value={form.base_url} onChange={(e) => setForm({ ...form, base_url: e.target.value })} placeholder="https://api.deepseek.com" required />
            <p className="text-xs text-muted-foreground">
              示例：{providers?.find((p) => p.provider === form.provider)?.example_base_url}
            </p>
          </div>
          <div className="space-y-2">
            <Label>模型名</Label>
            <Input value={form.model} onChange={(e) => setForm({ ...form, model: e.target.value })} placeholder="deepseek-v4-flash" required />
          </div>
          <div className="space-y-2">
            <Label>API 密钥 {form.id && <span className="text-muted-foreground">（留空则不修改）</span>}</Label>
            <Input type="password" value={form.api_key} onChange={(e) => setForm({ ...form, api_key: e.target.value })} placeholder="sk-..." />
          </div>
          <div className="flex items-center gap-6">
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={form.is_default} onChange={(e) => setForm({ ...form, is_default: e.target.checked })} />
              设为默认
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={form.enabled} onChange={(e) => setForm({ ...form, enabled: e.target.checked })} />
              <Power className="h-3 w-3" /> 启用
            </label>
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>取消</Button>
            <Button type="submit" disabled={saveMutation.isPending}>{saveMutation.isPending ? "保存中…" : "保存"}</Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}
