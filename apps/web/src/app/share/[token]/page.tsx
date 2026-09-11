"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Sparkles } from "lucide-react";
import { api, assetUrl } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

interface ShareData {
  review_id: string;
  title: string | null;
  decision: string;
  assets: { id: string; file_url: string | null; prompt: string; model: string }[];
  votes: { asset_id: string; vote: string }[];
}

const DECISION: Record<string, string> = {
  pending: "待定",
  approved: "已通过",
  rejected: "已驳回",
  on_hold: "待定中",
};

export default function SharePage() {
  const params = useParams<{ token: string }>();
  const { data, isLoading } = useQuery({
    queryKey: ["share", params.token],
    queryFn: () => api.get<ShareData>(`/share/${params.token}`),
  });

  return (
    <div className="mx-auto max-w-5xl p-6">
      <header className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-primary" />
          <h1 className="text-xl font-semibold">{data?.title ?? "评审分享"}</h1>
        </div>
        {data && <Badge variant={data.decision === "approved" ? "success" : data.decision === "rejected" ? "destructive" : "secondary"}>{DECISION[data.decision] ?? data.decision}</Badge>}
      </header>

      {isLoading ? (
        <p className="text-muted-foreground">加载中…</p>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {(data?.assets ?? []).map((a) => {
            const likes = (data?.votes ?? []).filter((v) => v.asset_id === a.id && v.vote === "like").length;
            return (
              <Card key={a.id} className="overflow-hidden">
                <div className="aspect-square bg-muted">
                  {a.file_url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={assetUrl(a.file_url)} alt={a.prompt} className="h-full w-full object-contain" />
                  ) : (
                    <div className="flex h-full items-center justify-center text-muted-foreground">暂无图片</div>
                  )}
                </div>
                <CardContent className="p-3">
                  <p className="line-clamp-2 text-xs text-muted-foreground">{a.prompt}</p>
                  <p className="mt-1 text-xs text-muted-foreground">👍 {likes} · {a.model}</p>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
