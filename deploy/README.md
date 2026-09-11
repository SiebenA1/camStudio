# 部署到阿里云 ECS（个人服务器）

本目录提供把 RealFrame Studio 部署到阿里云个人服务器（ECS）的完整方案：**Nginx 反代 + systemd 托管**（无需 Docker，最稳妥）。

## 0. 部署架构

```
浏览器
  │  https://your-domain.com
  ▼
Nginx (80/443)
  ├─ /          → 前端 Next.js   (127.0.0.1:3000)
  ├─ /api/      → 后端 FastAPI   (127.0.0.1:8787)
  └─ /files/    → 图片文件        (127.0.0.1:8787/files)
```

后端只监听 `127.0.0.1`，由 Nginx 对外反代，安全且便于加 HTTPS。

> 重要：本项目把空镜图以 **base64 内联** 发给 AI 模型（见 `gateway.py`），因此**服务器不需要对 AI 服务商开放公网图片访问**，个人 ECS 无需公网 IP 也能正常出图。

---

## 1. 服务器准备（一次性）

假设系统为 Ubuntu 22.04 / Debian 12（阿里云 Linux 3 亦可，命令用 `dnf` 替代）。

### 1.1 阿里云控制台
1. 购买 ECS（2 核 4G 即可起步）。
2. **安全组**放行端口：`22`（SSH）、`80`、`443`。
3. 若有域名，把域名 A 记录解析到 ECS 公网 IP。

### 1.2 安装基础软件

> 阿里云 ECS 访问国外源常超时，npm/pip 请务必用国内镜像。

```bash
ssh root@<你的公网IP>

# 系统更新（ROS2 等历史仓库报错可忽略，apt 会自动跳过）
apt update && apt upgrade -y

# Node.js：若已装（node -v 有输出）则跳过；否则用国内源
if ! command -v node >/dev/null; then
  curl -fsSL https://mirrors.aliyun.com/nodejs-release/ >/dev/null 2>&1 || true
  # 上面命令仅示意；更稳妥：用 nvm 国内镜像安装
  curl -o- https://gitee.com/mirrors/nvm/raw/master/install.sh | bash
  export NVM_DIR="$HOME/.nvm" && . "$NVM_DIR/nvm.sh"
  export NVM_NODEJS_ORG_MIRROR=https://mirrors.aliyun.com/nodejs-release/
  nvm install 20
fi

# npm 国内镜像 + pnpm
npm config set registry https://registry.npmmirror.com
npm install -g pnpm@11.25.0

# Python（Ubuntu 24.04 自带 3.12，用 python3 即可）+ Nginx 等
apt install -y python3 python3-venv python3-pip nginx rsync curl

# 验证
node -v && python3 --version && pnpm -v && nginx -v
```

### 1.3 创建运行用户与目录

```bash
useradd -m -s /bin/bash realframe
mkdir -p /opt/realframe /var/log/realframe
chown realframe:realframe /var/log/realframe
```

---

## 2. 上传代码

在**本地开发机**（Windows 用 scp / WinSCP / git 均可），把项目推到服务器：

```bash
# 方式 A：rsync（在服务器上执行，从本地拉取需保证网络可达；简单起见也可用 git）
git clone <你的仓库地址> /opt/realframe

# 方式 B：本地打包上传
# Windows:  tar -czf realframe.tar.gz --exclude=node_modules --exclude=.venv --exclude=data .
# 然后 scp realframe.tar.gz root@<IP>:/opt/ 并解压到 /opt/realframe
```

> 若用本目录的 `deploy.sh`，它已内置 rsync 同步逻辑（含排除 node_modules/.venv/data 等）。

---

## 3. 部署后端

```bash
cd /opt/realframe/apps/api

# 3.1 创建虚拟环境并安装依赖（用阿里 pip 镜像加速）
python3 -m venv .venv
.venv/bin/pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/
.venv/bin/pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 3.2 写配置（务必先做，见下方“关键注意”）
cp ../../deploy/.env.production.example .env
chmod 600 .env
nano .env   # 改 SECRET_KEY、STORAGE_BASE_URL、DATABASE_URL

# 3.3 数据目录
mkdir -p data/uploads
chown -R realframe:realframe /opt/realframe/apps/api

# 3.4 安装 systemd 服务并启动
cp ../../deploy/realframe-api.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now realframe-api
systemctl status realframe-api
curl http://127.0.0.1:8787/health   # 返回 {"status":"ok",...}
```

首次启动会自动建表 + 写入默认管理员 `admin@realframe.local / admin123`。

---

## 4. 部署前端

```bash
# 4.1 构建期环境变量（NEXT_PUBLIC_* 会被打包进前端，必须先设置）
mkdir -p /opt/realframe/apps/web
cat > /opt/realframe/apps/web/.env.production <<'EOF'
NEXT_PUBLIC_API_URL=https://your-domain.com/api/v1
EOF

# 4.2 在 workspace 根目录安装依赖（monorepo，须在根目录执行）+ 构建
cd /opt/realframe
pnpm config set registry https://registry.npmmirror.com
pnpm install
pnpm --filter @realframe/web build

# 4.3 安装 systemd 服务并启动
cd /opt/realframe
cp deploy/realframe-web.service /etc/systemd/system/
chown -R realframe:realframe /opt/realframe/apps/web
systemctl daemon-reload
systemctl enable --now realframe-web
systemctl status realframe-web
```

> 没有域名时：`NEXT_PUBLIC_API_URL=http://<公网IP>/api/v1`，且后端 `.env` 里 `STORAGE_BASE_URL=http://<公网IP>/files`。

---

## 5. Nginx 反向代理

```bash
cp /opt/realframe/deploy/nginx-realframe.conf /etc/nginx/conf.d/realframe.conf
nano /etc/nginx/conf.d/realframe.conf   # 把 your-domain.com 换成你的域名/IP

nginx -t
systemctl reload nginx
```

现在访问 `http://your-domain.com` 应该能看到登录页。

---

## 6. HTTPS（推荐，用于生产）

用 Certbot 申请免费证书：

```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d your-domain.com
```

Certbot 会自动改写 Nginx 配置并续期。之后把：
- 前端 `.env.production` 的 `NEXT_PUBLIC_API_URL` 改为 `https://your-domain.com/api/v1` 并 **重新 `pnpm build` + 重启 web**；
- 后端 `.env` 的 `STORAGE_BASE_URL` 改为 `https://your-domain.com/files` 并重启 api。

> 也可用阿里云免费 SSL 证书（云产品 → 数字证书管理），下载 nginx 版证书后手动配置。

---

## 7. 日常运维

```bash
# 查看状态 / 日志
systemctl status realframe-api realframe-web
tail -f /var/log/realframe/api.log
tail -f /var/log/realframe/web.log

# 重启 / 停止
systemctl restart realframe-api realframe-web
systemctl stop realframe-api realframe-web

# 备份（SQLite 数据库 + 图片）
tar -czf backup-$(date +%F).tar.gz -C /opt/realframe/apps/api data
```

### 更新部署
把新代码同步到服务器后执行（本目录已提供一键脚本）：

```bash
sudo DOMAIN=your-domain.com bash /opt/realframe/deploy/deploy.sh
```

或手动：`pnpm build`（前端）→ `pip install -r requirements.txt`（后端，如依赖变化）→ `systemctl restart realframe-api realframe-web`。

---

## 8. 关键注意 ⚠️

1. **SECRET_KEY 一旦定下不要改**：模型 API Key 是用它派生的密钥加密存 DB 的，中途换掉会导致已填的 Key 无法解密（需在界面重新填写）。生产务必设成长随机串：`openssl rand -hex 32`。
2. **NEXT_PUBLIC_API_URL 是构建期变量**：改它必须重新 `pnpm build` 才生效。
3. **STORAGE_BASE_URL 决定图片能否显示**：必须是对外可达的 `https://域名/files`（或 `http://IP/files`）。
4. **默认管理员密码**：上线后立刻登录改掉，或在 `app/core/seed.py` 里改默认账号后重建数据库。
5. **SQLite 单机足够**；若要多人高并发，把 `DATABASE_URL` 换成 PostgreSQL（表结构由启动时 `create_all` 自动创建）。
6. **CORS**：当前代码开发态为 `allow_origins=["*"]`；生产建议在 `app/main.py` 收紧为你的域名。

---

## 9. 常见问题

| 现象 | 排查 |
|---|---|
| 图片裂了 | 检查 `STORAGE_BASE_URL` 是否对外可达、Nginx `/files/` 是否配置 |
| API 调用失败 | `tail /var/log/realframe/api.log`；确认后端 `.env` 模型 Key 已填 |
| 前端白屏 | `tail /var/log/realframe/web.log`；确认 `pnpm build` 成功、Nginx `/` 指向 3000 |
| 上传大图失败 | 调大 Nginx `client_max_body_size` |
| 端口被墙 | 阿里云安全组确认放行 80/443 |

---

## 附：Docker 方式（可选）

如果更想用容器，可自行编写：后端用 `python:3.12-slim` 跑 `uvicorn`、前端用 `node:20-alpine` 分「build → run」两阶段、再挂一个 nginx 容器做反代；数据卷挂 `/data`。因 Next.js pnpm monorepo 的容器构建较繁琐，个人单机更推荐上面的 systemd 方案。
