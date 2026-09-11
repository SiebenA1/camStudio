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
  analysis_json: PhotoAnalysis | null;
  guidance_json: Guidance | null;
  status: string;
  created_at: string;
}

// 模特照片分析结果
export interface PhotoAnalysis {
  scene?: { type?: string; background?: string };
  lighting?: { direction?: string; temperature?: string; intensity?: string; note?: string };
  model?: { gender?: string; age?: string; style?: string; pose?: string; expression?: string };
  outfit?: { clothing?: string; accessories?: string[]; colors?: string[] };
  props?: string[];
  composition?: { rule?: string; angle?: string; note?: string };
  color?: { palette?: string[]; mood?: string };
  improvement?: string[];
  [key: string]: unknown;
}

// 推荐相机拍摄参数
export interface CameraParams {
  aperture?: string;
  shutter_speed?: string;
  iso?: string;
  focal_length?: string;
  white_balance?: string;
  drive_mode?: string;
  note?: string;
  [key: string]: unknown;
}

export interface Guidance {
  camera_params?: CameraParams;
  elements?: { pose?: string; expression?: string; composition?: string };
  pose_variations?: string[];
  risk_tips?: string[];
  [key: string]: unknown;
}

// 拍摄设备配置
export interface EquipmentSpecs {
  camera?: { model?: string; sensor?: string; resolution?: string; iso_range?: string; shutter_range?: string; sync_speed?: string };
  lens?: { model?: string; focal_range?: string; max_aperture?: string; stabilization?: string };
  note?: string;
  [key: string]: unknown;
}

export interface EquipmentProfile {
  camera_model: string | null;
  lens_model: string | null;
  specs: EquipmentSpecs | null;
  updated_at: string | null;
}

// 预定义姿势/动作风格
export interface PoseStyle {
  id: string;
  label: string;
  hint: string;
}

// 相机/镜头型号目录（按品牌分组）
export interface CatalogGroup {
  brand: string;
  models: string[];
}

export interface EquipmentCatalog {
  cameras: CatalogGroup[];
  lenses: CatalogGroup[];
}

export const TASK_TYPE_LABELS: Record<string, string> = {
  chat: "文本",
  vision: "视觉评分",
  image: "文生图",
  video: "文生视频",
  embed: "向量化",
};
