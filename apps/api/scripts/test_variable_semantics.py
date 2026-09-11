"""测试：输入变量语义（只 3 类）+ 自定义服装输入。"""
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.project import Variable


def main() -> None:
    with TestClient(app) as client:
        token = client.post("/api/v1/auth/login", json={"email": "admin@realframe.local", "password": "admin123"}).json()["data"]["access_token"]
        h = {"Authorization": f"Bearer {token}"}
        pid = client.post("/api/v1/projects", json={"name": "变量语义测试"}, headers=h).json()["data"]["id"]

        # 模拟 brief 拆解落库结果：只插入 3 类输入变量
        db = SessionLocal()
        for i, t in enumerate(["character", "outfit", "scene"]):
            db.add(Variable(project_id=pid, type=t, options=["A", "B"], selected=["A"], weight=0.8, sort=i))
        db.commit()
        db.close()

        vs = client.get(f"/api/v1/projects/{pid}/variables", headers=h).json()["data"]
        print("变量类型:", [v["type"] for v in vs])

        # 自定义服装输入：追加 option 并选中
        outfit = next(v for v in vs if v["type"] == "outfit")
        r = client.patch(f"/api/v1/projects/{pid}/variables/{outfit['id']}",
                         json={"options": [*outfit["options"], "用户手输：米白色亚麻衬衫"], "selected": ["用户手输：米白色亚麻衬衫"]}, headers=h)
        d = r.json()["data"]
        print("自定义后 options:", d["options"])
        print("选中:", d["selected"])


if __name__ == "__main__":
    main()
