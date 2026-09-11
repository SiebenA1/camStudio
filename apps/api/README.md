# RealFrame Studio API

FastAPI 后端。详见仓库根 `README.md` 与 `docs/refined-design.md`。

## 安装与启动（Windows）

```bash
# 在 apps/api 目录下
python -m venv --without-pip .venv
python -m pip install --no-cache-dir --target .venv/Lib/site-packages -r requirements.txt

# 启动（端口 8787）
.venv/Scripts/python.exe -m uvicorn app.main:app --app-dir . --reload --port 8787
```

> 说明：本地沙箱环境无法用 `ensurepip` 创建带 pip 的 venv，因此用 `--without-pip` + `--target` 方式安装。
> 后续新增依赖：`python -m pip install --no-cache-dir --target .venv/Lib/site-packages <pkg>`

## 配置

复制 `.env.example` 为 `.env` 可覆盖配置（数据库、密钥、CORS 等）。

## 测试

```bash
$env:PYTHONPATH = (Get-Location).Path
.venv/Scripts/python.exe scripts/smoke_test.py
```

## 目录

```
app/
├─ main.py            # 入口（lifespan 建表 + 种子 + worker）
├─ config.py          # 配置
├─ database.py        # 引擎/会话
├─ models/            # SQLAlchemy 模型
├─ schemas/           # Pydantic schema
├─ api/               # 路由（auth/projects/previz/reviews/admin_models）
├─ core/              # 安全/审计/错误/存储/种子
├─ services/          # brief 拆解 / 预演编排 / 评分
├─ ai/                # 模型网关 + Provider 适配器
└─ workers/           # 后台任务 worker
```
