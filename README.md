# RealFrame Studio

面向商业摄影全流程的「AI 预演 + 实拍定稿」智能化协作平台。

用 **AI 预演** 在成本最低阶段锁定视觉方向，用 **真实拍摄** 守住品质与合规底线，把「预演 → 评审 → 验证 → 实拍 → 后期 → 交付」串成一条可管理、可追溯、可复用的智能流水线。

> 详细设计见 [`docs/refined-design.md`](docs/refined-design.md)。

---

## 已落地的 MVP（Phase 1）

- **项目 / Brief 中心**：项目 CRUD、Brief 导入（文本/PDF/PPT）、AI 六类变量拆解（人物/穿搭/场景/姿势/表情/构图）、变量矩阵调整。
- **AI 预演引擎**：模型网关（多 Provider 适配）、**空镜图生预演**（上传实拍空镜图 → 视觉分析场景 → 生成拍摄指导与要素 → 图生图合成主体）、文生图异步生成、任务队列 + 后台 worker、质量评分（视觉模型打分）、版本与成本记录。
- **评审中心**：并排对比、批注打分、投票、审批流、客户分享链接（公开只读页）。
- **模型配置**：管理界面统一配置国内大模型（文本/视觉/文生图/向量），支持 OpenAI 兼容与 DashScope 异步接口，含连通性测试。

## 技术栈

| 层 | 选型 |
|---|---|
| 前端 | Next.js 16 (App Router, Turbopack) + React 19 + TypeScript + Tailwind v4 + TanStack Query + Zustand |
| 后端 | FastAPI + SQLAlchemy 2.0 + Pydantic v2 |
| 数据库 | SQLite（默认，零依赖）→ 可切 PostgreSQL + pgvector |
| 队列 | 进程内 asyncio worker（DB 队列）→ 可切 Redis + Celery/arq |
| 模型 | 国内优先：DeepSeek / 通义千问 / 智谱 GLM / 万相 / 可灵（见 `docs/refined-design.md` §10） |

## 目录结构

```
camTest/
├─ apps/
│  ├─ web/          # Next.js 前端（@realframe/web）
│  └─ api/          # FastAPI 后端（Python）
├─ docs/            # 设计文档
└─ package.json     # pnpm workspace 根
```

---

## 快速开始

### 环境要求
- Node.js ≥ 20，pnpm ≥ 9
- Python 3.12+（本项目在 3.14 验证通过）

### 1. 后端

```bash
cd apps/api

# 创建虚拟环境并安装依赖（Windows）
python -m venv --without-pip .venv
python -m pip install --no-cache-dir --target .venv/Lib/site-packages -r requirements.txt

# 启动（端口 8787）
.venv/Scripts/python.exe -m uvicorn app.main:app --app-dir . --reload --port 8787
```

> 首次启动会自动建表并写入种子数据（默认租户 + 管理员 + 7 条默认模型配置）。
> 数据库文件位于 `apps/api/data/realframe.db`，生成图片位于 `apps/api/data/uploads/`。

### 2. 前端

```bash
# 仓库根目录
pnpm install
pnpm dev:web          # 或 cd apps/web && pnpm dev
```

前端默认运行在 `http://localhost:3000`，通过 `NEXT_PUBLIC_API_URL` 访问后端（默认 `http://localhost:8787/api/v1`，可在 `apps/web/.env.local` 覆盖）。

### 3. 登录

默认管理员：`admin@realframe.local` / `admin123`

---

## 配置国内大模型

1. 登录后进入「模型配置」页面。
2. 系统已预置默认模型（API Key 留空）：
   - 文本：DeepSeek `deepseek-v4-flash`（备选 通义千问 / 智谱 GLM）
   - 视觉评分：DeepSeek `deepseek-v4-flash-vision-exp`
   - 文生图：阿里万相 `wan2.7-image-pro`（备选 `qwen-image-3.0-pro`）
   - 向量化：智谱 `embedding-3`
3. 点击「编辑」填入对应平台的 API Key，点「测试」验证连通性，点「新增模型」可加入其他国内模型。

各模型接口要点（已独立核实，详见 `docs/refined-design.md` §10）：

| 能力 | 首选默认 | Base URL | 接口类型 |
|---|---|---|---|
| 文本 | deepseek-v4-flash | https://api.deepseek.com | OpenAI 兼容 |
| 视觉 | deepseek-v4-flash-vision-exp | https://api.deepseek.com | OpenAI 兼容 |
| 文生图 | wan2.7-image-pro | https://dashscope.aliyuncs.com | DashScope 异步 |
| 向量 | embedding-3 | https://open.bigmodel.cn/api/paas/v4 | OpenAI 兼容 |

---

## 核心 API（`/api/v1`）

```
POST /auth/login | /auth/register | GET /auth/me
POST/GET /projects | GET/PATCH/DELETE /projects/{id}
POST /projects/{id}/brief | POST /projects/{id}/brief/file | POST /projects/{id}/brief/parse
GET /projects/{id}/variables | PATCH /projects/{id}/variables/{vid}
POST /projects/{id}/previz/generate | GET /projects/{id}/previz | GET /previz/{asset_id}
POST /previz/{asset_id}/score | GET /tasks/{task_id}
POST /projects/{id}/reviews | GET /reviews/{id}
POST /reviews/{id}/comments | /votes | /approvals | /share
GET /share/{token}          （公开）
GET/POST /admin/models | PATCH/DELETE /admin/models/{id} | POST /admin/models/{id}/test
GET /admin/models/providers
```

统一响应 `{ code, message, data, request_id }`，`code === 0` 表示成功。

---

## 路线图

- **Phase 1（已完成 MVP）**：项目/Brief、AI 预演、评审、模型配置。
- **Phase 2**：消费者验证、实拍执行、后期合成、合规标识（C2PA 预研）。
- **Phase 3**：资产库 + 向量检索、模型路由优化、开放 API、区块链存证、移动端深化。
