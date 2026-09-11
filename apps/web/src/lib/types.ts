// 与后端对齐的类型定义

export interface User {
  id: string;
  tenant_id: string;
  email: string;
  name: string;
  role: string;
  status: string;
  is_superuser: boolean;
}

export interface AuthData {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Project {
  id: string;
  tenant_id: string;
  name: string;
  brand: string | null;
  status: string;
  owner_id: string | null;
  budget: number | null;
  timeline: Record<string, unknown> | null;
  description: string | null;
  created_at: string;
  updated_at: string;
  brief?: Brief | null;
}

export interface Brief {
  id: string;
  source_type: string;
  raw_text: string;
  parsed_json: Record<string, unknown> | null;
  status: string;
}

export interface Variable {
  id: string;
  type: string;
  options: string[];
  selected: string[];
  weight: number;
  sort: number;
}

export interface PrevizAsset {
  id: string;
  project_id: string;
  combo_id: string | null;
  model: string;
  provider: string;
  prompt: string;
  prompt_hash: string;
  seed: number | null;
  params: Record<string, unknown>;
  file_url: string | null;
  thumbnail_url: string | null;
  video_url: string | null;
  status: string;
  quality_score: number | null;
  quality_detail: Record<string, unknown> | null;
  cost: number;
  version: number;
  ai_ratio: number;
  error: string | null;
  created_at: string;
  updated_at: string;
}

export interface ModelConfig {
  id: string;
  tenant_id: string;
  provider: string;
  name: string;
  base_url: string;
  api_key_masked: string;
  model: string;
  task_type: string;
  is_default: boolean;
  enabled: boolean;
  extra: Record<string, unknown>;
}

export interface Review {
  id: string;
  project_id: string;
  asset_ids: string[];
  reviewer_id: string | null;
  type: string;
  status: string;
  decision: string;
  title: string | null;
  share_token: string | null;
  comments: ReviewComment[];
  votes: ReviewVote[];
  approvals: Approval[];
  assets?: PrevizAssetSummary[];
  created_at: string;
}

export interface ReviewComment {
  id: string;
  review_id: string;
  author_id: string | null;
  author_name: string | null;
  asset_id: string | null;
  kind: string;
  shape: Record<string, unknown> | null;
  text: string;
  score: number | null;
  resolved: boolean;
  created_at: string;
}

export interface ReviewVote {
  id: string;
  asset_id: string;
  vote: string;
  voter_key: string;
}

export interface Approval {
  id: string;
  actor_name: string | null;
  decision: string;
  comment: string | null;
  created_at: string;
}

export interface PrevizAssetSummary {
  id: string;
  file_url: string | null;
  prompt: string;
  model: string;
  quality_score: number | null;
}

export interface ReferenceShot {
  id: string;
  project_id: string;
  file_url: string;
  filename: string | null;
  analysis_json: SceneAnalysis | null;
  guidance_json: Guidance | null;
  status: string;
  created_at: string;
}

export interface SceneAnalysis {
  scene_type?: string;
  lighting?: { direction?: string; temperature?: string; intensity?: string; note?: string };
  camera?: { angle?: string; height?: string; lens_suggestion?: string };
  space?: { subject_zone?: string; free_area?: string };
  composition?: { vanishing_point?: string; rule?: string; note?: string };
  color?: { palette?: string[]; mood?: string };
  props?: string[];
  challenge?: string;
  [key: string]: unknown;
}

export interface Guidance {
  camera_plan?: { subject_position?: string; camera_angle?: string; shooting_position?: string };
  shot_list?: { shot?: string; camera?: string; subject?: string; lighting?: string; note?: string }[];
  elements?: { character?: string; outfit?: string; pose?: string; expression?: string; composition?: string };
  lighting_setup?: string;
  props_needed?: string[];
  risk_tips?: string[];
  [key: string]: unknown;
}

export const VARIABLE_LABELS: Record<string, string> = {
  character: "人物",
  outfit: "穿搭 / 服装",
  scene: "场景",
  pose: "姿势",
  expression: "表情",
  composition: "构图",
};

// 用户指定的创作输入（场景由空镜图本身决定，不再作为输入）
export const INPUT_VARIABLE_TYPES = ["character", "outfit"];
// 由工具推导的专业参数（不由用户指定）
export const DERIVED_VARIABLE_TYPES = ["pose", "expression", "composition", "position", "angle"];

export const TASK_TYPE_LABELS: Record<string, string> = {
  chat: "文本",
  vision: "视觉评分",
  image: "文生图",
  video: "文生视频",
  embed: "向量化",
};
