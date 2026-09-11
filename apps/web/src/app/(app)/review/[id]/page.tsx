"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Check, ExternalLink, ThumbsDown, ThumbsUp, X } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";
import { api, assetUrl } from "@/lib/api";
import type { Review } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn, formatDateTime } from "@/lib/utils";

const DECISION_META: Record<string, { label: string; variant: "secondary" | "success" | "destructive" | "warning" }> = {
  pending: { label: "待定", variant: "secondary" },
  approved: { label: "已通过", variant: "success" },
  rejected: { label: "已驳回", variant: "destructive" },
  on_hold: { label: "待定中", variant: "warning" },
};

export default function ReviewPage() {
  const params = useParams<{ id: string }>();
  const reviewId = params.id;
  const qc = useQueryClient();
  const [commentText, setCommentText] = useState("");
  const [commentScore, setCommentScore] = useState(5);
  const [activeAsset, setActiveAsset] = useState<string | null>(null);
  const [approvalComment, setApprovalComment] = useState("");

  const { data: review } = useQuery({
    queryKey: ["review", reviewId],
    queryFn: () => api.get<Review>(`/reviews/${reviewId}`),
  });

  const commentMutation = useMutation({
    mutationFn: () =>
      api.post(`/reviews/${reviewId}/comments`, {
        text: commentText,
        score: commentScore,
        asset_id: activeAsset,
        kind: "text",
      }),
    onSuccess: () => {
      setCommentText("");
      toast.success("批注已添加");
      qc.invalidateQueries({ queryKey: ["review", reviewId] });
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "添加失败"),
  });

  const voteMutation = useMutation({
    mutationFn: ({ assetId, vote }: { assetId: string; vote: string }) =>
      api.post(`/reviews/${reviewId}/votes`, { asset_id: assetId, vote }),
    onSuccess: () => {
      toast.success("已投票");
      qc.invalidateQueries({ queryKey: ["review", reviewId] });
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "投票失败"),
  });

  const approvalMutation = useMutation({
    mutationFn: (decision: string) =>
      api.post(`/reviews/${reviewId}/approvals`, { decision, comment: approvalComment }),
    onSuccess: () => {
      toast.success("审批已记录");
      setApprovalComment("");
      qc.invalidateQueries({ queryKey: ["review", reviewId] });
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "审批失败"),
  });

  const shareMutation = useMutation({
    mutationFn: () => api.post<{ url: string; share_token: string }>(`/reviews/${reviewId}/share`, {}),
    onSuccess: (r) => {
      const url = `${window.location.origin}${r.url}`;
      navigator.clipboard?.writeText(url);
      toast.success(`分享链接已复制：${url}`);
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "生成失败"),
  });

  if (!review) return <div className="text-muted-foreground">加载评审…</div>;

  const meta = DECISION_META[review.decision] ?? DECISION_META.pending;
  const assets = review.assets ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Link href="/projects" className="mb-2 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
            <ArrowLeft className="h-4 w-4" /> 返回
          </Link>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-semibold">{review.title ?? "评审"}</h1>
            <Badge variant={meta.variant}>{meta.label}</Badge>
          </div>
        </div>
        <Button variant="outline" onClick={() => shareMutation.mutate()} disabled={shareMutation.isPending}>
          <ExternalLink /> 生成客户分享链接
        </Button>
      </div>

      {/* 对比视图 */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {assets.map((a) => {
          const votes = review.votes.filter((v) => v.asset_id === a.id);
          const likes = votes.filter((v) => v.vote === "like").length;
          return (
            <Card key={a.id} className={cn("overflow-hidden", activeAsset === a.id && "ring-2 ring-primary")}>
              <div
                className="relative aspect-square cursor-pointer bg-muted"
                onClick={() => setActiveAsset(activeAsset === a.id ? null : a.id)}
              >
                {a.file_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={assetUrl(a.file_url)} alt={a.prompt} className="h-full w-full object-contain" />
                ) : (
                  <div className="flex h-full items-center justify-center text-muted-foreground">暂无图片</div>
                )}
                {a.quality_score != null && (
                  <Badge variant="default" className="absolute left-2 top-2">{Math.round(a.quality_score)} 分</Badge>
                )}
              </div>
              <CardContent className="space-y-2 p-3">
                <p className="line-clamp-2 text-xs text-muted-foreground">{a.prompt}</p>
                <div className="flex items-center justify-between">
                  <div className="flex gap-1">
                    <Button size="sm" variant="outline" onClick={() => voteMutation.mutate({ assetId: a.id, vote: "like" })}>
                      <ThumbsUp className="h-3.5 w-3.5" /> {likes}
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => voteMutation.mutate({ assetId: a.id, vote: "dislike" })}>
                      <ThumbsDown className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                  <span className="text-xs text-muted-foreground">{a.model}</span>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* 批注 */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">批注与打分</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">评分：</span>
                {[1, 2, 3, 4, 5].map((s) => (
                  <button key={s} onClick={() => setCommentScore(s)} className={cn("text-xl", s <= commentScore ? "text-amber-400" : "text-muted")}>
                    ★
                  </button>
                ))}
              </div>
              <Textarea
                value={commentText}
                onChange={(e) => setCommentText(e.target.value)}
                placeholder={activeAsset ? "对当前选中图片的批注…" : "整体批注…（点击上方图片可针对单图批注）"}
                rows={2}
              />
              <Button size="sm" onClick={() => commentMutation.mutate()} disabled={!commentText.trim() || commentMutation.isPending}>
                添加批注
              </Button>
            </div>
            <div className="space-y-2">
              {review.comments.map((c) => (
                <div key={c.id} className="rounded-md border p-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium">{c.author_name ?? "匿名"}</span>
                    <span className="text-xs text-muted-foreground">
                      {c.score ? `${"★".repeat(c.score)} ` : ""}
                      {formatDateTime(c.created_at)}
                    </span>
                  </div>
                  <p className="mt-1 text-sm">{c.text}</p>
                </div>
              ))}
              {!review.comments.length && <p className="text-sm text-muted-foreground">暂无批注</p>}
            </div>
          </CardContent>
        </Card>

        {/* 审批 */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">审批决策</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Textarea
              value={approvalComment}
              onChange={(e) => setApprovalComment(e.target.value)}
              placeholder="审批意见（可选）"
              rows={2}
            />
            <div className="flex gap-2">
              <Button onClick={() => approvalMutation.mutate("approved")} className="bg-emerald-600 hover:bg-emerald-700">
                <Check /> 通过
              </Button>
              <Button variant="destructive" onClick={() => approvalMutation.mutate("rejected")}>
                <X /> 驳回
              </Button>
              <Button variant="outline" onClick={() => approvalMutation.mutate("on_hold")}>
                待定
              </Button>
            </div>
            <div className="space-y-2">
              {review.approvals.map((a) => (
                <div key={a.id} className="flex items-center gap-2 text-sm">
                  <Badge variant={a.decision === "approved" ? "success" : a.decision === "rejected" ? "destructive" : "warning"}>
                    {a.decision}
                  </Badge>
                  <span className="text-muted-foreground">{a.actor_name}</span>
                  {a.comment && <span className="text-muted-foreground">— {a.comment}</span>}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
