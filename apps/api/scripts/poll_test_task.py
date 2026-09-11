"""轮询测试任务，验证 poll 端点路径与结果解析格式。"""
import sqlite3
import time

import httpx

from app.core.security import decrypt_secret

TASK_ID = "89acda1f-5db2-4d06-893e-177e100b0dbd"


def main() -> None:
    conn = sqlite3.connect("data/realframe.db")
    row = conn.execute(
        "SELECT api_key FROM model_configs WHERE task_type='image' AND is_default=1"
    ).fetchone()
    conn.close()
    key = decrypt_secret(row[0])

    url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{TASK_ID}"
    h = {"Authorization": f"Bearer {key}"}
    for i in range(8):
        r = httpx.get(url, headers=h, timeout=30)
        data = r.json()
        out = data.get("output") or {}
        st = out.get("task_status")
        print(f"poll {i + 1}: http={r.status_code} task_status={st}")
        if st in ("SUCCEEDED", "FAILED"):
            urls = [
                c.get("image")
                for ch in out.get("choices", [])
                for c in ch.get("message", {}).get("content", [])
                if c.get("type") == "image"
            ]
            print("  image_urls:", urls[:1])
            print("  usage:", out.get("usage"))
            break
        time.sleep(6)


if __name__ == "__main__":
    main()
