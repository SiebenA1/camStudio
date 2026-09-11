"""测试：一次生成 3 张不同姿势的框架示意图。"""
import io

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app


def _png() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), (120, 140, 160)).save(buf, format="PNG")
    return buf.getvalue()


def main() -> None:
    with TestClient(app) as client:
        token = client.post("/api/v1/auth/login", json={"email": "admin@realframe.local", "password": "admin123"}).json()["data"]["access_token"]
        h = {"Authorization": f"Bearer {token}"}
        pid = client.post("/api/v1/projects", json={"name": "框架图测试"}, headers=h).json()["data"]["id"]

        shot = client.post(f"/api/v1/projects/{pid}/reference-shots", headers=h,
                           files={"file": ("a.png", _png(), "image/png")}).json()["data"]

        # 触发生成（无指导时走默认 3 姿势）
        r = client.post(f"/api/v1/reference-shots/{shot['id']}/generate", headers=h)
        data = r.json()["data"]
        print("generate code:", r.json()["code"], "asset_ids:", len(data["asset_ids"]), "poses:", data["poses"])

        # 验证资产提示词各不相同
        assets = client.get(f"/api/v1/projects/{pid}/previz", headers=h).json()["data"]
        print("assets count:", len(assets))
        for a in assets:
            print("  prompt 前30字:", a["prompt"][:30])


if __name__ == "__main__":
    main()
