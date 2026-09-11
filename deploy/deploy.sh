#!/usr/bin/env bash
# RealFrame Studio 一键部署 / 更新脚本（阿里云 ECS，Ubuntu/Debian）
# 用法：
#   sudo bash deploy/deploy.sh            # 首次部署或更新
# 前提：已按 deploy/README.md 完成第 1 步（安装依赖、创建 realframe 用户与目录）
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/realframe}"
REPO_DIR="${REPO_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
DOMAIN="${DOMAIN:-}"   # 可选：传入域名用于提示

echo "==> 同步代码到 ${APP_DIR}"
sudo rsync -a --delete \
  --exclude '.git' --exclude 'node_modules' --exclude '.next' \
  --exclude '.venv' --exclude 'data' --exclude '.pnpm-store' \
  --exclude '.pnpm-cache' --exclude '.tmp' \
  "${REPO_DIR}/" "${APP_DIR}/"

echo "==> 部署后端"
cd "${APP_DIR}/apps/api"
if [ ! -d .venv ]; then
  sudo -u realframe python3 -m venv .venv
fi
sudo -u realframe .venv/bin/pip install -q --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/
sudo -u realframe .venv/bin/pip install -q -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
sudo -u realframe mkdir -p data/uploads

if [ ! -f .env ]; then
  echo "!! 未找到 .env —— 正在从模板生成，请务必修改 SECRET_KEY / STORAGE_BASE_URL 后重跑"
  sudo -u realframe cp "${REPO_DIR}/deploy/.env.production.example" .env
  sudo -u realframe chmod 600 .env
  echo "!! 编辑：nano ${APP_DIR}/apps/api/.env"
  exit 1
fi

echo "==> 部署前端"
cd "${APP_DIR}"
# NEXT_PUBLIC_API_URL 在构建时被写入前端包，必须先设置好
if [ ! -f apps/web/.env.production ]; then
  if [ -z "${DOMAIN}" ]; then
    echo "!! 请先创建 ${APP_DIR}/apps/web/.env.production，内容："
    echo "   NEXT_PUBLIC_API_URL=https://your-domain.com/api/v1"
    exit 1
  fi
  echo "NEXT_PUBLIC_API_URL=https://${DOMAIN}/api/v1" | sudo -u realframe tee apps/web/.env.production >/dev/null
fi
sudo -u realframe pnpm config set registry https://registry.npmmirror.com
sudo -u realframe pnpm install
sudo -u realframe pnpm --filter @realframe/web build

echo "==> 重启服务"
sudo systemctl restart realframe-api realframe-web
sudo systemctl --no-pager --lines=0 status realframe-api realframe-web || true

echo "==> 完成。健康检查："
curl -fsS http://127.0.0.1:8787/health || echo "(后端未就绪，请查看 /var/log/realframe/api.log)"
echo
