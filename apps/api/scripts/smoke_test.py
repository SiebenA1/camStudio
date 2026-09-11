"""后端冒烟测试：健康检查、登录、项目 CRUD、模型配置列表。"""
from fastapi.testclient import TestClient

from app.main import app


def main() -> None:
    with TestClient(app) as client:
        # 健康检查
        r = client.get("/health")
        print("health:", r.status_code, r.json())

        # 登录（默认管理员）
        r = client.post("/api/v1/auth/login", json={"email": "admin@realframe.local", "password": "admin123"})
        print("login:", r.status_code, r.json().get("code"))
        token = r.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 创建项目
        r = client.post("/api/v1/projects", json={"name": "测试项目", "brand": "TestBrand", "description": "冒烟测试"}, headers=headers)
        print("create project:", r.status_code, r.json().get("code"), r.json().get("data", {}).get("name"))
        pid = r.json()["data"]["id"]

        # 导入 brief
        r = client.post(f"/api/v1/projects/{pid}/brief", json={"source_type": "text", "raw_text": "一个年轻女性在阳光下的咖啡馆，穿着米色风衣，微笑看向镜头"}, headers=headers)
        print("import brief:", r.status_code, r.json().get("code"))

        # 项目列表
        r = client.get("/api/v1/projects", headers=headers)
        print("list projects:", r.status_code, "count:", len(r.json()["data"]))

        # 模型配置列表
        r = client.get("/api/v1/admin/models", headers=headers)
        print("models:", r.status_code, "count:", len(r.json()["data"]))
        for m in r.json()["data"]:
            print("  ", m["task_type"], m["provider"], m["model"], "default=", m["is_default"])

        # providers
        r = client.get("/api/v1/admin/models/providers", headers=headers)
        print("providers:", r.status_code, [p["provider"] for p in r.json()["data"]])

        # 变量列表（应为空，未解析）
        r = client.get(f"/api/v1/projects/{pid}/variables", headers=headers)
        print("variables:", r.status_code, r.json()["data"])


if __name__ == "__main__":
    main()
