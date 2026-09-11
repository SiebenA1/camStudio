"""用已配置的 Key 实测万相端点是否正确。"""
import json
import sqlite3

import httpx

from app.core.security import decrypt_secret


def main() -> None:
    conn = sqlite3.connect("data/realframe.db")
    row = conn.execute(
        "SELECT base_url, api_key, model FROM model_configs WHERE task_type='image' AND is_default=1"
    ).fetchone()
    conn.close()
    base_url, api_key, model = row
    key = decrypt_secret(api_key) if api_key else ""
    print(f"当前 base_url = {base_url!r}")
    print(f"model = {model}, key 前缀 = {key[:6]}")

    # 正确的根地址
    root = "https://dashscope.aliyuncs.com"
    url = f"{root}/api/v1/services/aigc/image-generation/generation"
    body = {
        "model": model,
        "input": {"messages": [{"role": "user", "content": [{"text": "一只猫"}]}]},
        "parameters": {"size": "1K", "n": 1, "watermark": False},
    }
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json", "X-DashScope-Async": "enable"}
    print("\n测试正确地址...")
    try:
        r = httpx.post(url, headers=headers, json=body, timeout=60)
        print("status:", r.status_code)
        print("body:", r.text[:400])
        if r.status_code == 200:
            data = r.json()
            task_id = (data.get("output") or {}).get("task_id")
            print("SUCCESS task_id =", task_id)
    except Exception as e:
        print("ERR", e)


if __name__ == "__main__":
    main()
