"""测试：项目导出 ZIP（含数据与图片）+ 项目删除。"""
import io
import zipfile

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app


def _png() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (48, 48), (90, 120, 150)).save(buf, format="PNG")
    return buf.getvalue()


def main() -> None:
    with TestClient(app) as client:
        token = client.post("/api/v1/auth/login", json={"email": "admin@realframe.local", "password": "admin123"}).json()["data"]["access_token"]
        h = {"Authorization": f"Bearer {token}"}
        pid = client.post("/api/v1/projects", json={"name": "导出测试项目", "brand": "DemoBrand"}, headers=h).json()["data"]["id"]

        # 放一张空镜图 + 一个预演资产
        client.post(f"/api/v1/projects/{pid}/reference-shots", headers=h,
                    files={"file": ("shot.png", _png(), "image/png")})
        client.post(f"/api/v1/projects/{pid}/previz/generate", json={"count": 1}, headers=h)

        # 导出
        r = client.get(f"/api/v1/projects/{pid}/export", headers=h)
        print("export status:", r.status_code, "content-type:", r.headers.get("content-type"))
        print("Content-Disposition:", r.headers.get("content-disposition"))
        zf = zipfile.ZipFile(io.BytesIO(r.content))
        names = zf.namelist()
        print("ZIP 内容:", names)
        import json as _json
        data = _json.loads(zf.read("project.json"))
        print("project.json keys:", list(data.keys()))
        print("项目名:", data["project"]["name"], "资产数:", len(data["previz_assets"]), "空镜图数:", len(data["reference_shots"]))

        # 删除
        r = client.delete(f"/api/v1/projects/{pid}", headers=h)
        print("delete:", r.json()["code"], r.json()["message"])
        left = client.get("/api/v1/projects", headers=h).json()["data"]
        print("删除后该项目是否还在列表:", any(p["id"] == pid for p in left))


if __name__ == "__main__":
    main()
