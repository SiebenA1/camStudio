"""测试：设备配置 CRUD + 模特照片上传（不触发 AI 调用）。"""
import io

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app


def _png() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), (150, 120, 100)).save(buf, format="PNG")
    return buf.getvalue()


def main() -> None:
    with TestClient(app) as client:
        token = client.post("/api/v1/auth/login", json={"email": "admin@realframe.local", "password": "admin123"}).json()["data"]["access_token"]
        h = {"Authorization": f"Bearer {token}"}

        # 设备：GET 初始 + PUT 设置
        r = client.get("/api/v1/admin/equipment", headers=h)
        print("equipment GET:", r.json()["code"], "camera=", r.json()["data"]["camera_model"])
        r = client.put("/api/v1/admin/equipment", json={"camera_model": "Canon EOS R5", "lens_model": "RF 24-70mm F2.8L"}, headers=h)
        d = r.json()["data"]
        print("equipment PUT:", r.json()["code"], "camera=", d["camera_model"], "lens=", d["lens_model"], "specs=", d["specs"])

        # 上传模特照片
        pid = client.post("/api/v1/projects", json={"name": "模特照片流程"}, headers=h).json()["data"]["id"]
        r = client.post(f"/api/v1/projects/{pid}/reference-shots", headers=h,
                        files={"file": ("model.png", _png(), "image/png")})
        print("upload:", r.json()["code"], "status=", r.json()["data"]["status"])

        # 换设备型号后 specs 应被清空（验证"型号变了需重新获取"）
        r = client.put("/api/v1/admin/equipment", json={"camera_model": "Sony A7M4"}, headers=h)
        print("换型号后 specs:", r.json()["data"]["specs"])


if __name__ == "__main__":
    main()
