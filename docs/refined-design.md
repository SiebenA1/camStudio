# RealFrame Studio 开发设计文档（细化完善版 v1.0）

> 本文档在「简要版」基础上细化、修正与落地化，作为后续开发与评审的单一事实来源（Single Source of Truth）。
> 版本：v1.0　｜　状态：已评审待开发　｜　更新：以 git 提交历史为准

---

## 0. 文档目的与阅读对象

- 目的：把产品定位转化为「可直接开发」的技术方案，消除歧义、明确边界、给出可执行的 MVP 与演进路线。
- 阅读对象：产品、前后端工程师、算法/模型接入、法务合规、项目管理者。

---

## 1. 产品定位与核心假设（重新审视）

### 1.1 一句话定位
**用 AI 预演在成本最低阶段锁定视觉方向，用实拍守住品质与合规底线，把「预演 → 验证 → 实拍 → 后期 → 交付」串成一条可管理、可追溯、可复用的智能流水线。**

### 1.2 核心价值主张（价值排序）
1. **降本**：在未开拍前完成方向验证，避免昂贵实拍的返工。
2. **提效**：预演、评审、验证、实拍、后期在同一工作区流转，减少跨工具搬运。
3. **合规可追溯**：AI 标识、C2PA、RAW 哈希存证贯穿全链路。
4. **复用**：验证过的场景/光线/姿态/Prompt 沉淀为品牌资产。

### 1.3 明确的「不做什么」（防蔓延）
- **不替代**摄影师/修图师，只提供预演参考与工作台。
- **不承诺**「AI 直接出商业终稿」——商业宣传主图必须实拍或以实拍为主体，AI 仅做辅助标注。
- **不做**社交化图片社区、素材交易市场。
- **不做**自有模型训练（MVP 阶段只做模型路由/编排）。

### 1.4 边界与假设（Assumptions）
| 编号 | 假设 | 影响 |
|---|---|---|
| A1 | 客户主要在桌面 Web 使用，现场参考用移动端 H5（非原生 App） | 前端优先 Web，移动端用响应式 + PWA |
| A2 | MVP 单租户→多租户渐进；租户间数据强隔离 | RBAC 从简起步，表结构预留 tenant_id |
| A3 | 外部模型均走 API 计费，需在界面配置 API Key | 模型配置表 + 管理界面为一级功能 |
| A4 | 本地开发环境无 Docker/Postgres/Redis | 默认 SQLite，抽象层可切 PostgreSQL/pgvector/Redis |

---

## 2. 目标用户、角色与核心用户旅程

### 2.1 角色 × 权限矩阵（RBAC 初版）
| 角色 | 项目查看 | 预演生成 | 评审批注 | 评审终审 | 模型配置 | 成员管理 | 合规审查 |
|---|---|---|---|---|---|---|---|
| 品牌方/广告主 | 本租户项目 | ❌ | ✅ | ✅（决策） | ❌ | 本团队 | ✅ |
| 创意/策划 | 本租户项目 | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| 摄影师/制片 | 参与项目 | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ |
| 修图/合成师 | 参与项目 | ✅（后期资产） | ✅ | ❌ | ❌ | ❌ | ✅ |
| 法务/合规 | 本租户项目 | ❌ | 只读 | ✅（合规否决） | ❌ | ❌ | ✅ |
| 消费者验证 | 参与项目 | ❌ | ❌ | ❌ | ❌ | ❌ | 只读 |
| 管理员 | 全部 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

> 权限模型：`tenant → project → role`，MVP 用「租户级角色 + 项目级成员」两级，后续扩展 ABAC。

### 2.2 核心用户旅程（Happy Path）
1. **建项目**：品牌方/创意新建项目，导入 Brief（粘贴文本 / 上传 PDF/PPT）。
2. **拆变量**：AI 把 Brief 拆成六类变量（人物/穿搭/场景/姿势/表情/构图），生成变量矩阵，人工调权重。
3. **预演**：选择变量组合 → 生成静帧方案（多模型路由）→ 对锁定方案生成 3-5 秒动态镜头。
4. **内部评审**：批注/打分/对比，收敛到 3-5 套方案。
5. **客户评审**：生成分享链接 → 客户投票/审批/电子签 → 锁定方向。
6. **（可选）消费者验证**：由锁定方案自动生成问卷，回收指标，出对比看板。
7. **实拍**：由锁定方案生成通告单/shot list/清单；现场移动端对照预演；RAW 自动上传存证。
8. **后期**：AI 环境资产 + 实拍主体合成，图层对齐，人工精修，终稿审批。
9. **交付**：合规标识 + C2PA + RAW 哈希存证 + 交付包归档。

> MVP 落地范围：旅程 1-5 全链路 + 旅程 7/8/9 的「数据结构与占位」；旅程 6 与 7-9 的完整功能在 Phase 2/3。

---

## 3. 功能模块细化（含 MVP 边界）

### 3.1 项目与 Brief 中心（Phase 1）
- **Brief 导入**：粘贴文本；上传 PDF/PPT（解析为文本，OCR 可选）。
- **AI 变量拆解**：调用文本大模型，输出结构化六类变量 + 权重（可调），落库 `variable` 表。
  - 六类变量：`character`(人物)、`outfit`(穿搭)、`scene`(场景)、`pose`(姿势)、`expression`(表情)、`composition`(构图)。
  - 每类变量含 `options[]`（候选值）+ `selected`（当前选中）+ `weight`（0-1）。
- **变量矩阵**：笛卡尔积可视化，支持勾选组合、批量生成。
- **项目看板**：状态机、成员、预算、时间线（甘特式）。

### 3.2 AI 预演生成引擎（Phase 1 核心）
> **核心范式（已修正）**：预演不止「纯文生图」，而是**基于真实空镜图的图生预演** —— 摄影师先拍一张空镜图（空场景/空机位）上传，系统据此给出拍摄预演指导，而非凭空生成。
- **空镜图生预演**：上传实拍空镜图 → 视觉模型分析场景（光线/机位/透视/色彩/可用空间/道具）→ 结合 Brief 生成拍摄指导（shot list/机位/灯光/构图）与要素（人物/穿搭/姿势/表情/构图）→ 以空镜图为参考图生图，把主体合成进真实场景。
- **Prompt 模板库**：变量槽位 `{{var.character}}` 等；模板可存资产库复用（用于纯文生图补充场景）。
- **模型路由**：按任务类型（文生图/图生图(参考图)/图生视频/视觉评分/文本）路由到已配置的国内模型。
- **异步任务**：生成任务入队 → 轮询/回调 → 状态机 `pending→running→succeeded|failed`。
- **质量初筛**：视觉模型打分（构图/清晰度/品牌色偏差），低分自动置后，人工终筛。
- **版本管理**：每次生成保留 `prompt/seed/model/params/cost/status`，支持回滚对比。
- **动态预演**：图生视频，输出 3-5 秒关键镜头（Phase 1 可选，Phase 2 深化）。
- **成本追踪**：每次调用记录 token/图片数/费用，聚合到项目与租户。

### 3.3 评审与协同中心（Phase 1）
- **内部评审**：Konva 画布批注（框选/箭头/文字）、1-5 星打分、并排对比视图。
- **客户评审**：生成带 token 的分享链接，匿名/实名投票、审批流（通过/驳回/待定）、电子签（Phase 2）。
- **实时协作**：WebSocket 同步批注与状态（MVP 可降级为轮询，接口预留 WS）。
- **决策归档**：评审记录 + 结论自动写入项目时间线，作为决策依据。

### 3.4 消费者验证中心（Phase 2）
- 由锁定方案自动生成问卷；对接问卷平台/焦点小组；回收「品牌信任感、价格匹配度、购买意愿」等指标；数据看板（对比、显著性检验、推荐方向）。

### 3.5 实拍执行管理（Phase 2）
- 由锁定方案生成通告单、shot list、设备/模特/场地清单；移动端现场对照；RAW 自动上传（GPS/时间/设备指纹/哈希）；拍摄日志与合规声明自动生成。

### 3.6 后期合成工作台（Phase 2）
- AI 环境资产生成；图层管理（透视/光影对齐）；人工精修分派；版本对比；输出 TIFF + Web JPEG。

### 3.7 合规与交付（Phase 2 起步，Phase 3 完整）
- **AI 参与度标注**：三档 `纯实拍 / AI 辅助（标注比例）/ AI 生成`，显式标识 + 隐式水印。
- **C2PA**：记录生成/拍摄/编辑历史（国内落地困难，先用自研 manifest + 哈希链，Phase 3 接 C2PA SDK）。
- **RAW 哈希存证**：SHA-256 + 时间戳，可选上链（Phase 3）。

### 3.8 资产库与复用（Phase 3）
- 已验证场景/光线/姿态/Prompt/品牌视觉规范沉淀；跨项目调用；标签 + 向量检索（pgvector）。

### 3.9 管理后台（Phase 1 起步）
- 多租户、RBAC、团队管理；**模型配置（一级功能）**；成本/利润统计；审计日志；数据加密。

---

## 4. 系统架构（细化 + 落地约束修正）

```
客户端（Web / 移动端 H5）
        │  HTTPS / WSS
API 网关（Auth JWT / 限流 / 路由 / CORS）   ← FastAPI 内置，生产可换 Envoy/Nginx
        │
应用服务层（单体起步，模块化，可拆微服务）：
  项目 | 预演 | 评审 | 验证 | 拍摄 | 后期 | 合规 | 资产 | 配置
        │
AI 编排层（Prompt 编排 / 任务队列 / 模型路由）
        │
模型网关（统一 Provider 接口）→ 国内模型（DeepSeek/Qwen/GLM/Kimi/豆包/万相/可灵…）
        │
数据层：SQLAlchemy ORM
  ├─ 默认 SQLite（本地 MVP，零依赖）
  └─ 生产 PostgreSQL + pgvector（配置切换）
  缓存/队列：MVP 用 DB 队列 + 内存缓存；生产 Redis + Celery/arq（接口抽象）
  存储：本地磁盘（MVP）/ S3 / MinIO（生产，接口抽象）
```

### 4.1 关键落地决策（相对简要版的修正）
| 简要版 | 细化版决策 | 理由 |
|---|---|---|
| 微服务 8 个 | 单体模块化起步，接口边界即服务边界 | MVP 提速，团队小；未来按模块拆 |
| PostgreSQL + Redis + Temporal 硬要求 | SQLite + DB 队列默认，抽象层可切 | 本地无 Docker/Postgres，保证「今天能跑」 |
| 模型网关 | Provider 适配器 + 配置表 + 管理界面 | 满足「模型配置在界面完成」 |
| C2PA SDK 直接集成 | 自研 manifest + 哈希，Phase 3 接 C2PA | 国内 C2PA 生态不成熟 |

### 4.2 关键横切设计
1. **预演生成异步化**：DB 队列表 + 后台 worker（进程内调度，可切 Celery）。
2. **模型网关统一接口**：`generate_image / generate_video / chat / score_image / embed`，便于替换与成本控制。
3. **实时协作**：FastAPI WebSocket（MVP 预留，可降级轮询）。
4. **合规元数据贯穿**：所有生成物携带 `ai_ratio`、`model`、`prompt_hash`、`seed`。
5. **审计日志**：所有写操作记录 `who/when/what/before/after`。

---

## 5. 数据模型（细化，含约束与索引）

> 约定：所有表含 `id`(UUID 或自增)、`created_at`、`updated_at`、`deleted_at`(软删)、`tenant_id`(多租户预留)。

| 实体 | 关键字段（细化） | 关系 |
|---|---|---|
| **Tenant** | id, name, slug, plan, status | 1:N 其余所有 |
| **User** | id, tenant_id, email, name, password_hash, role, status | N:M Project(member) |
| **Project** | id, tenant_id, name, brand, brief_text, status(enum), owner_id, budget, timeline, team | 1:N 其余业务实体 |
| **Brief** | id, project_id, source_type(text/pdf/ppt), raw_text, parsed_json, status | 1:1 Project |
| **Variable** | id, project_id, type(enum 六类), options(json), selected(json), weight, sort | N:1 Project |
| **VariableCombo** | id, project_id, combo(json), weight | 用于矩阵生成 |
| **PromptTemplate** | id, tenant_id, name, task_type, template(text 含槽位), brand_id | 可复用 |
| **PrevizAsset** | id, project_id, combo_id, template_id, model, prompt, prompt_hash, seed, params(json), file_url, thumbnail_url, status(enum), quality_score, cost, version, ai_ratio, video_url | N:1 Project |
| **ReferenceShot** | id, project_id, file_url, filename, analysis_json(场景分析), guidance_json(拍摄指导+要素), status(uploaded/analyzed/guided) | 空镜图生预演 |
| **GenerationTask** | id, project_id, asset_id, task_type(enum), model, provider, params(json), status(enum), queue, error, cost, external_task_id, callback | 队列 |
| **Review** | id, project_id, asset_ids(json), reviewer_id, type(internal/client), status, decision(enum), share_token, expires_at | N:1 Project |
| **ReviewComment** | id, review_id, author_id, asset_id, kind(pin/rect/arrow/text), shape(json), text, score, resolved | N:1 Review |
| **ReviewVote** | id, review_id, voter_key, asset_id, vote(enum), created_at | 客户投票 |
| **Approval** | id, review_id, actor_id, decision(enum), comment, esign_ref, created_at | 审批流 |
| **Validation** | id, project_id, survey(json), responses(json), metrics(json), status | Phase 2 |
| **ShootPlan** | id, project_id, date, location, crew(json), equipment(json), shot_list(json), status | Phase 2 |
| **RawAsset** | id, shoot_id, file_url, metadata(json: gps/time/device), hash, status | Phase 2 |
| **Composite** | id, project_id, raw_asset_id, ai_assets(json), layers(json), status | Phase 2 |
| **Deliverable** | id, project_id, file_url, compliance_id, status | Phase 2 |
| **ComplianceRecord** | id, deliverable_id, ai_ratio, c2pa_manifest, watermark, raw_hash, status | Phase 2 |
| **AssetLibrary** | id, tenant_id, brand_id, type(enum), tags(json), prompt, file_url, embedding(vector), meta | Phase 3 |
| **ModelConfig** | id, tenant_id, provider(enum), name, base_url, api_key(加密), model, is_default, enabled, extra(json) | 一级功能 |
| **AuditLog** | id, tenant_id, actor_id, action, entity, entity_id, before(json), after(json), ip | 横切 |

### 5.1 枚举定义（初版）
- Project.status: `draft → briefing → previz → reviewing → locked → shooting → post → delivering → delivered / archived`
- PrevizAsset.status: `pending → generating → succeeded / failed / superseded`
- GenerationTask.status: `queued → running → succeeded / failed / cancelled`
- Review.type: `internal / client`
- Review.decision: `pending / approved / rejected / on_hold`
- Variable.type: `character / outfit / scene / pose / expression / composition`

---

## 6. API 契约（细化，OpenAPI）

> 前缀 `/api/v1`，统一响应 `{ code, message, data, request_id }`；错误码规范。

### 6.1 项目与 Brief
```
POST   /api/v1/projects                         创建项目
GET    /api/v1/projects                         项目列表（分页/筛选）
GET    /api/v1/projects/{id}                    项目详情
PATCH  /api/v1/projects/{id}                    更新项目
POST   /api/v1/projects/{id}/brief              导入 Brief（文本/文件）
POST   /api/v1/projects/{id}/brief/parse        触发 AI 变量拆解（异步）
GET    /api/v1/projects/{id}/variables          获取变量矩阵
PATCH  /api/v1/projects/{id}/variables/{vid}    调整变量/权重
POST   /api/v1/projects/{id}/combos             创建变量组合
```

### 6.2 预演引擎
```
GET    /api/v1/projects/{id}/templates          可选 Prompt 模板
POST   /api/v1/projects/{id}/previz/generate    提交生成任务（批量）
GET    /api/v1/projects/{id}/previz             预演资产列表
GET    /api/v1/previz/{asset_id}                单个资产详情（含版本）
POST   /api/v1/previz/{asset_id}/score          触发质量评分
POST   /api/v1/previz/{asset_id}/video          图生视频（动态预演）
GET    /api/v1/tasks/{task_id}                  任务状态
GET    /api/v1/projects/{id}/costs              成本汇总
```

### 6.3 评审
```
POST   /api/v1/projects/{id}/reviews            创建评审
GET    /api/v1/reviews/{id}                     评审详情（含批注/投票）
POST   /api/v1/reviews/{id}/comments            新增批注
POST   /api/v1/reviews/{id}/votes               投票
POST   /api/v1/reviews/{id}/approvals           审批
POST   /api/v1/reviews/{id}/share               生成客户分享链接
GET    /api/v1/share/{token}                    匿名查看评审（客户）
WS     /api/v1/ws/reviews/{id}                  实时同步（预留）
```

### 6.4 模型配置（管理后台）
```
GET    /api/v1/admin/models                     模型配置列表
POST   /api/v1/admin/models                     新增模型配置
PATCH  /api/v1/admin/models/{id}                更新（含 API Key）
DELETE /api/v1/admin/models/{id}                删除
POST   /api/v1/admin/models/{id}/test           连通性测试
GET    /api/v1/admin/models/providers           可用 Provider 清单
```

### 6.5 管理
```
GET/POST/PATCH/DELETE /api/v1/admin/users        用户管理
GET    /api/v1/admin/audit-logs                 审计日志
GET    /api/v1/admin/costs                      成本统计
```

---

## 7. AI 预演引擎设计（细化）

### 7.1 处理流水线
```
Brief + 变量矩阵 + 品牌规范
   → Prompt 模板匹配（变量填充）
   → 模型路由（按 task_type + 项目/租户默认配置）
   → 生成任务入队（异步）
   → 批量生成
   → 质量初筛（视觉评分：清晰度/构图/品牌色）
   → 动态预演（图生视频，可选）
   → 成本 + 版本记录
   → 输出：3-5 套方案 + 动态镜头 + 成本报告
```

### 7.2 模型路由规则
1. 优先取项目级覆盖配置，其次租户默认，再次系统默认。
2. 按 `task_type` 映射 Provider：`text→chat`、`image→文生图`、`image_edit→图生图`、`video→图生视频`、`score→视觉`、`embed→向量`。
3. 失败自动降级到同类型的备用模型（可配）。
4. 成本上限：项目/租户预算阈值触发熔断告警。

### 7.3 质量评分（国内落地替代 CLIP）
- 用多模态视觉模型（如 Qwen-VL / GLM-4V / 豆包视觉）做结构化评分：`清晰度、构图合理性、品牌色一致、风格匹配`，返回 JSON 分数（0-100）。
- 可选叠加本地 CLIP 相似度（对品牌参考图），Phase 2。

### 7.4 一致性保障
- 固定 `seed`、`prompt_hash`、`model`、`params` 保证可复现；版本链 `version` 递增。

---

## 8. 合规与安全（细化，务实）

### 8.1 国内法规对齐
- 《生成式人工智能服务管理暂行办法》：AI 生成内容显式标识。
- 《互联网信息服务深度合成管理规定》：深度合成内容显著标识 + 溯源。
- 《广告法》：真实代言、不得虚假宣传；预演禁用真实名人可识别肖像。

### 8.2 落地机制（MVP → 完整）
| 能力 | MVP | Phase 2/3 |
|---|---|---|
| AI 显式标识 | 生成物渲染角标 + 元数据 | 全链路 UI 标识 |
| 隐式水印 | 盲水印库（开源） | 商业盲水印 |
| 内容溯源 | 自研 manifest（prompt_hash/model/seed/时间）+ 哈希链 | C2PA SDK |
| RAW 存证 | SHA-256 哈希 + 审计日志 | 区块链存证（可选） |
| 肖像合规 | 预演生成提示词强制「非真实名人」负向词 | 合规扫描（名人库比对） |

### 8.3 安全基线
- JWT 认证 + 租户隔离（查询强制 `tenant_id` 过滤）。
- API Key 加密存储（Fernet/AES）。
- RBAC + 审计日志；上传文件 MIME/大小校验。
- 敏感字段脱敏（日志不回显 API Key）。

---

## 9. 技术栈（细化，含版本与理由）

| 层级 | 选型 | 版本/说明 | 理由 |
|---|---|---|---|
| 前端 | Next.js + TypeScript | 15（App Router） | SSR/生态/招人 |
| UI | Tailwind + shadcn/ui | 最新 | 快速出质量 |
| 画布批注 | Konva + react-konva | 最新 | 批注/对比 |
| 状态/请求 | Zustand + TanStack Query | 最新 | 轻量/缓存 |
| 后端 | FastAPI | 0.11x | AI 生态/Pydantic |
| ORM | SQLAlchemy 2.0 + Alembic | 最新 | 类型化/迁移 |
| 校验 | Pydantic v2 | 最新 | 契约清晰 |
| 数据库 | SQLite（默认）/ PostgreSQL + pgvector | 生产 | 本地可跑/生产强 |
| 队列 | DB 队列（默认）/ Redis + arq/Celery | 抽象 | 无 Docker 可跑 |
| 存储 | 本地磁盘（默认）/ S3/MinIO | 抽象 | 同上 |
| 实时 | WebSocket（FastAPI）| 预留 | 协作 |
| AI 编排 | 自研 Provider 适配器 | 见 §7 | 国内多模型统一 |
| 合规 | 盲水印库 + 自研 manifest | Phase 2 | 国内 C2PA 不成熟 |
| 部署 | Docker + K8s（生产）| 本地裸跑 | 云可迁 |

> **关键决策：国内大模型优先**。文本/视觉/文生图/文生视频/Embedding 均选国内 Provider（详见 §10），模型接入参数通过管理界面配置，不硬编码。

---

## 10. 国内大模型选型（已独立验证 · 2026 年当前官方口径）

> 调研结论：任务书中的模型名大多已换代更名，本表以「当前官方在售代际」为准。核实等级：✅ 官方文档核实；🟡 稳定公开值/第三方量级参照。
> 关键结构差异：**文本/视觉/Embedding 均走 OpenAI 兼容 `chat.completions`/`embeddings` 接口**；**文生图/文生视频是「提交任务 + 轮询结果」的异步接口**，需按供应商写适配层。

### 10.1 文本大模型
| 供应商 | base_url（OpenAI 兼容） | 当前模型 | 上下文 | 备注 |
|---|---|---|---|---|
| DeepSeek ✅ | `https://api.deepseek.com` | `deepseek-v4-flash` / `deepseek-v4-pro` | 1M | 官方价格透明、最便宜；`deepseek-reasoner` 已并入 thinking 模式 |
| 阿里 Qwen ✅ | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen3.8-max` / `qwen3.7-plus` / `qwen3.8-flash` | — | 支持 function call/JSON 输出 |
| 智谱 GLM ✅ | `https://open.bigmodel.cn/api/paas/v4` | `glm-5.3` / `glm-5.3-flash` / `glm-5.2` | 1M | glm-5.3 始终思考；glm-5.3-flash 原生多模态 |
| Kimi 🟡 | `https://api.moonshot.cn/v1` | `kimi-k3` | 1M | 国内/海外双域 |
| 豆包/火山 🟡 | `https://ark.cn-beijing.volces.com/api/v3` | `doubao-seed-2.1-pro` / `2.0-mini` | — | 单价需控制台确认 |

### 10.2 多模态视觉理解（质量评分 / 图生文）
| 供应商 | 模型 | 图像输入 | 结构化评分 |
|---|---|---|---|
| DeepSeek ✅ | `deepseek-v4-flash-vision-exp` | JPEG/PNG/GIF/WebP，base64 或 URL | ✅ JSON 输出 |
| 阿里 ✅ | `qwen3.8-max` / `qwen3.7-plus`（已原生多模态） | ✅ image_url | ✅ function call |
| 智谱 ✅ | `glm-5.3-flash`（多模态）/ `glm-ocr` | ✅ | ✅ 结构化输出 |

### 10.3 文生图（异步任务接口）
| 供应商 | 当前模型 | 返回 | 图生图/参考图 |
|---|---|---|---|
| 阿里万相 ✅ | `wan2.7-image-pro` / `qwen-image-3.0-pro` | URL（临时） | ✅ 参考图/编辑/控制 |
| 智谱 ✅ | `glm-image`（原 CogView） | URL | ✅ |
| 豆包 🟡 | `doubao-seedream-4.0` | URL | ✅ |
| 百度 🟡 | `ernie-vilg-v2` | URL/base64 | 参考图，控制弱 |

### 10.4 文生/图生视频（异步任务接口）
| 供应商 | 当前模型 | 时长/分辨率 |
|---|---|---|
| 可灵 Kling ✅ | `kling-3.0` / `2.6-pro` | 5s/10s，720p/1080p |
| 豆包 Seedance 🟡 | `doubao-seedance-2.0-mini`（降本）/ `1.5-pro` | 支持 4K |
| 阿里万相 ✅ | `wan3.0-video` / `happyhorse-1.1-i2v` | — |

### 10.5 Embedding（资产库检索）
| 供应商 | 模型 | 维度 | 价格 |
|---|---|---|---|
| 智谱 ✅ | `embedding-3` | 256–2048 可调 | 0.5 元/百万 tokens（官方核实） |
| 阿里 ✅ | `text-embedding-v4` | 以控制台为准 | 未核实 |

### 10.6 推荐默认选型（模型配置界面的系统默认清单）
| 能力 task_type | 首选默认 | 备选 | 接口类型 |
|---|---|---|---|
| `chat`（文本） | `deepseek-v4-flash` | `qwen3.7-plus` / `glm-5.3-flash` | OpenAI 兼容 |
| `vision`（视觉评分） | `deepseek-v4-flash-vision-exp` | `qwen3.7-plus` / `glm-5.3-flash` | OpenAI 兼容 |
| `image`（文生图） | 阿里 `wan2.7-image-pro` | 豆包 `doubao-seedream-4.0` / 智谱 `glm-image` | DashScope 异步 |
| `video`（图生视频） | 可灵 `kling-3.0` | 豆包 `doubao-seedance-2.0-mini` | Kling 异步 |
| `embed`（向量） | 智谱 `embedding-3` | 阿里 `text-embedding-v4` | OpenAI 兼容 |

### 10.7 C2PA / 盲水印落地结论
- 国内官方：阿里云「AI 数智鉴密（AI DeepSign）」提供 C2PA 签名/校验 API（Phase 3 候选）。
- 开源自部署：`AI45Lab/UniMark`（多模态盲水印）、`unStone/digital-watermarking`（前端 C2PA 读取 + LSB/频域盲水印）。
- 结论：盲水印不能作为唯一溯源手段，C2PA 签名是更强方案；MVP 用「显式标识 + 自研 manifest + 哈希链」，Phase 3 接 C2PA。

### 10.8 待二次确认（非阻塞）
阿里 qwen3.x 各档单价、火山方舟人民币单价、智谱 GLM-5.3 单价、Kimi K3 单价、可灵国内 endpoint 与人民币每秒价 —— 均需在对应控制台最终确认，不影响本阶段开发（模型均通过配置界面可改）。

---

## 11. MVP 路线图（细化到可交付物）

### Phase 1（0-3 月，本次落地目标）
- **M1 骨架**：monorepo、前后端跑通、健康检查、鉴权登录、租户/用户种子。
- **M2 配置**：模型配置 CRUD + 连通性测试界面。
- **M3 项目/Brief**：项目 CRUD、Brief 导入、AI 变量拆解、变量矩阵。
- **M4 预演**：模型网关、文生图异步生成、资产列表/详情、版本、成本。
- **M5 评审**：内部评审批注/打分/对比、客户分享链接/投票/审批、决策归档。
- **M6 打磨**：审计日志、成本看板、启动文档、端到端联调。

### Phase 2（3-6 月）
消费者验证、实拍执行、后期合成、合规标识、C2PA 预研。

### Phase 3（6-12 月）
资产库 + 向量检索、模型路由优化、开放 API、区块链存证、移动端深化。

### 关键指标（KPI）
- 预演到定稿周期缩短 ≥ 30%
- 方向错误率下降 ≥ 50%
- 客户评审轮次减少 ≥ 40%
- 合规审查通过率 100%

---

## 12. 主要风险与对策（细化）

| 风险 | 触发 | 对策 |
|---|---|---|
| 模型成本波动 | 高频生成 | 多模型路由 + 预算熔断 + 结果缓存复用 |
| 生成质量不稳定 | 模型出图差 | 视觉评分初筛 + 人工终筛 + 版本回滚 + 固定 seed |
| 国内模型接口变更 | 供应商改 API | Provider 适配器隔离 + 配置化 base_url/model |
| 法规变化 | 新规 | 合规模块可配置 + 法务审核流 + 审计留痕 |
| 数据安全 | 泄露 | 加密存储 + 租户隔离 + 审计日志 + 脱敏 |
| 无 Docker 本地环境 | 跑不起来 | SQLite/DB 队列/本地磁盘默认，抽象层可切生产 |
| C2PA 国内不成熟 | 无法认证 | 自研 manifest + 哈希链先落地，Phase 3 接 C2PA |

---

## 13. 附录

### 13.1 目录结构（monorepo 规划）
```
camTest/
├─ apps/
│  ├─ web/            # Next.js 前端
│  └─ api/            # FastAPI 后端
├─ packages/
│  └─ shared/         # 共享类型/枚举/常量（前后端复用）
├─ docs/              # 设计文档
└─ docker/            # 生产部署（Phase 2）
```

### 13.2 术语表
- **Previz（预演）**：Pre-visualization，实拍前的视觉方案预演。
- **变量矩阵**：六类变量的笛卡尔组合空间，用于批量生成候选。
- **C2PA**：Coalition for Content Provenance and Authenticity，内容来源认证标准。
- **RAW 存证**：原始拍摄文件的哈希 + 元数据固化，用于溯源与合规。

---

*本文档为 v1.0 细化版，待「国内模型选型」调研回填 §10 后定稿并进入开发。*
