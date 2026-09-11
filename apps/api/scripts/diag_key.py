"""诊断：模型配置的写入时间 + 触发一次生成验证服务进程能否读取 Key。"""
import time

import httpx

BASE = "http://localhost:8787/api/v1"


def main() -> None:
    import sqlite3
    conn = sqlite3.connect("data/realframe.db")
    print("=== image 配置 updated_at ===")
    for r in conn.execute(
        "SELECT name, model, is_default, updated_at FROM model_configs WHERE task_type='image' ORDER BY updated_at DESC"
    ):
        print(r)
    conn.close()

    # 触发一次生成，验证服务进程能否读到 Key（能读到则不会报 no_api_key）
    with httpx.Client(timeout=60) as c:
        r = c.post(f"{BASE}/auth/login", json={"email": "admin@realframe.local", "password": "admin123"})
        token = r.json()["data"]["access_token"]
        h = {"Authorization": f"Bearer {token}"}
        r = c.post(f"{BASE}/projects", json={"name": "key验证"}, headers=h)
        pid = r.json()["data"]["id"]
        r = c.post(f"{BASE}/projects/{pid}/previz/generate", json={"count": 1, "width": 1024, "height": 1024}, headers=h)
        print("generate:", r.json().get("code"), r.json().get("message"))
        time.sleep(6)
        r = c.get(f"{BASE}/projects/{pid}/previz", headers=h)
        for a in r.json()["data"]:
            print("  asset status:", a["status"], "error:", (a.get("error") or "")[:80])


if __name__ == "__main__":
    main()
