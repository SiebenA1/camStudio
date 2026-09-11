"""测试：预演图删除 + 空镜图更换/删除。"""
import io

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app


def _png() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), (200, 100, 100)).save(buf, format="PNG")
    return buf.getvalue()


def main() -> None:
    with TestClient(app) as client:
        token = client.post("/api/v1/auth/login", json={"email": "admin@realframe.local", "password": "admin123"}).json()["data"]["access_token"]
        h = {"Authorization": f"Bearer {token}"}
        pid = client.post("/api/v1/projects", json={"name": "删除测试"}, headers=h).json()["data"]["id"]

        # 上传空镜图
        shot = client.post(f"/api/v1/projects/{pid}/reference-shots", headers=h,
                           files={"file": ("a.png", _png(), "image/png")}).json()["data"]
        print("upload:", shot["status"])

        # 更换空镜图
        shot2 = client.post(f"/api/v1/reference-shots/{shot['id']}/replace", headers=h,
                            files={"file": ("b.png", _png(), "image/png")}).json()["data"]
        print("replace: status=", shot2["status"], "file_url_changed=", shot2["file_url"] != shot["file_url"])

        # 生成预演资产（不触发 AI，仅创建）
        gen = client.post(f"/api/v1/projects/{pid}/previz/generate", json={"count": 1}, headers=h).json()["data"]
        aid = gen["assets"][0]["id"]
        print("generate asset:", aid[:8])

        # 删除预演资产
        r = client.delete(f"/api/v1/previz/{aid}", headers=h)
        print("delete asset:", r.json()["code"], r.json()["message"])

        # 删除空镜图
        r = client.delete(f"/api/v1/reference-shots/{shot['id']}", headers=h)
        print("delete shot:", r.json()["code"], r.json()["message"])

        # 列表应为空
        shots = client.get(f"/api/v1/projects/{pid}/reference-shots", headers=h).json()["data"]
        previz = client.get(f"/api/v1/projects/{pid}/previz", headers=h).json()["data"]
        print("shots left:", len(shots), "previz left:", len(previz))


if __name__ == "__main__":
    main()
