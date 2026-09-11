"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FileText, Plus, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { INPUT_VARIABLE_TYPES, VARIABLE_LABELS, type Variable } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export function BriefPanel({ projectId }: { projectId: string }) {
  const qc = useQueryClient();
  const [text, setText] = useState("");
  const [addingType, setAddingType] = useState<string | null>(null);
  const [customValue, setCustomValue] = useState("");

  const { data: variables } = useQuery({
    queryKey: ["variables", projectId],
    queryFn: () => api.get<Variable[]>(`/projects/${projectId}/variables`),
  });

  const { data: project } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => api.get<{ brief?: { raw_text: string; status: string } | null }>(`/projects/${projectId}`),
  });

  useEffect(() => {
    if (project?.brief?.raw_text != null && text === "") {
      setText(project.brief.raw_text);
    }
  }, [project, text]);

  const saveMutation = useMutation({
    mutationFn: () => api.post(`/projects/${projectId}/brief`, { source_type: "text", raw_text: text }),
    onSuccess: () => {
      toast.success("Brief 已保存");
      qc.invalidateQueries({ queryKey: ["project", projectId] });
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "保存失败"),
  });

  const parseMutation = useMutation({
    mutationFn: () => api.post<Record<string, unknown>>(`/projects/${projectId}/brief/parse`, {}),
    onSuccess: () => {
      toast.success("输入变量已拆解（人物 / 服装）");
      qc.invalidateQueries({ queryKey: ["variables", projectId] });
      qc.invalidateQueries({ queryKey: ["project", projectId] });
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "拆解失败"),
  });

  const updateVariable = useMutation({
    mutationFn: ({ vid, selected, options }: { vid: string; selected?: string[]; options?: string[] }) =>
      api.patch(`/projects/${projectId}/variables/${vid}`, {
        ...(selected !== undefined ? { selected } : {}),
        ...(options !== undefined ? { options } : {}),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["variables", projectId] }),
    onError: (e) => toast.error(e instanceof Error ? e.message : "更新失败"),
  });

  // 只展示「用户可指定」的输入变量
  const inputVars = (variables ?? []).filter((v) => INPUT_VARIABLE_TYPES.includes(v.type));

  function addCustom(v: Variable) {
    const val = customValue.trim();
    if (!val) return;
    const options = v.options?.includes(val) ? v.options : [...(v.options ?? []), val];
    updateVariable.mutate({ vid: v.id, options, selected: [val] });
    setCustomValue("");
    setAddingType(null);
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-4 w-4" /> Brief 与输入变量
        </CardTitle>
        <CardDescription>
          你只需指定「人物 / 服装」；场景就是空镜图本身，拍摄位置、角度、姿势、表情、构图由工具推导
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <Textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="例如：面向 25-35 岁都市女性的春季轻奢风衣系列，场景为午后咖啡馆，自然光，整体氛围松弛高级…"
          rows={4}
        />
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => saveMutation.mutate()} disabled={saveMutation.isPending}>
            保存 Brief
          </Button>
          <Button onClick={() => parseMutation.mutate()} disabled={parseMutation.isPending || !text.trim()}>
            <Sparkles /> {parseMutation.isPending ? "拆解中…" : "AI 拆解输入变量"}
          </Button>
        </div>

        {inputVars.length > 0 && (
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            {inputVars.map((v) => (
              <div key={v.id} className="rounded-md border p-3">
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-sm font-medium">{VARIABLE_LABELS[v.type] ?? v.type}</span>
                  <Badge variant="outline">权重 {v.weight}</Badge>
                </div>
                <div className="flex flex-wrap items-center gap-1.5">
                  {(v.options ?? []).map((opt) => {
                    const active = v.selected?.includes(opt);
                    return (
                      <button
                        key={opt}
                        onClick={() => updateVariable.mutate({ vid: v.id, selected: active ? [] : [opt] })}
                        className={cn(
                          "rounded-full border px-2.5 py-0.5 text-xs transition-colors",
                          active
                            ? "border-primary bg-primary text-primary-foreground"
                            : "bg-muted text-muted-foreground hover:bg-accent"
                        )}
                      >
                        {opt}
                      </button>
                    );
                  })}
                  {addingType === v.type ? (
                    <span className="inline-flex items-center gap-1">
                      <Input
                        autoFocus
                        value={customValue}
                        onChange={(e) => setCustomValue(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") addCustom(v);
                          if (e.key === "Escape") { setAddingType(null); setCustomValue(""); }
                        }}
                        placeholder="自定义输入…"
                        className="h-7 w-36 text-xs"
                      />
                      <Button size="sm" className="h-7 px-2 text-xs" onClick={() => addCustom(v)}>确定</Button>
                    </span>
                  ) : (
                    <button
                      onClick={() => { setAddingType(v.type); setCustomValue(""); }}
                      className="inline-flex items-center gap-0.5 rounded-full border border-dashed px-2.5 py-0.5 text-xs text-muted-foreground hover:bg-accent"
                    >
                      <Plus className="h-3 w-3" /> 自定义
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        <p className="text-xs text-muted-foreground">
          说明：场景、拍摄位置、角度、姿势、表情、构图 均不在此处指定 —— 上传空镜图后，工具会分析场景并推导出合适的拍摄位置与角度，给出 3 个不同姿势的草图。
        </p>
      </CardContent>
    </Card>
  );
}
