"""空镜图生预演流程测试：上传 → 分析 → 指导 → 图生预演。"""
import io

import httpx
from PIL import Image

BASE = "http://localhost:8787/api/v1"


def main() -> None:
    with httpx.Client(timeout=60) as c:
        # 登录
        r = c.post(f"{BASE}/auth/login", json={"email": "admin@realframe.local", "password": "admin123"})
        token = r.json()["data"]["access_token"]
        h = {"Authorization": f"Bearer {token}"}
        print("login:", r.json()["code"])

        # 建项目
        r = c.post(f"{BASE}/projects", json={"name": "空镜预演测试"}, headers=h)
        pid = r.json()["data"]["id"]
        print("project:", pid[:8])

        # 生成一张测试空镜图（灰蓝渐变，模拟空场景）
        buf = io.BytesIO()
        img = Image.new("RGB", (640, 480), (120, 140, 160))
        img.save(buf, format="PNG")
        buf.seek(0)

        # 上传空镜图
        r = c.post(f"{BASE}/projects/{pid}/reference-shots", headers=h,
                   files={"file": ("empty_shot.png", buf, "image/png")})
        shot = r.json()["data"]
        print("upload:", r.json()["code"], "shot:", shot["id"][:8], "status:", shot["status"])

        # 列表
        r = c.get(f"{BASE}/projects/{pid}/reference-shots", headers=h)
        print("list count:", len(r.json()["data"]))

        # 分析（无 API Key 应优雅报错）
        r = c.post(f"{BASE}/reference-shots/{shot['id']}/analyze", headers=h)
        body = r.json()
        print("analyze:", r.status_code, body.get("code"), body.get("message", "")[:60])

        # 指导（未分析应先报 not_analyzed）
        r = c.post(f"{BASE}/reference-shots/{shot['id']}/guidance", headers=h)
        body = r.json()
        print("guidance:", r.status_code, body.get("code"), body.get("message", "")[:60])

        # 图生预演（应创建 pending 资产，worker 随后因无 Key 标记 failed）
        r = c.post(f"{BASE}/reference-shots/{shot['id']}/generate", headers=h)
        body = r.json()
        print("generate:", r.status_code, body.get("code"), body.get("data", {}).get("asset_id", "")[:8])


if __name__ == "__main__":
    main()
