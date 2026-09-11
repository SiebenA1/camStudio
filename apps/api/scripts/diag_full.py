"""诊断：查看 image 配置的 base_url 与失败任务的完整错误。"""
import sqlite3

from app.core.security import decrypt_secret


def main() -> None:
    conn = sqlite3.connect("data/realframe.db")
    print("=== image 配置（base_url / key 解密后前缀）===")
    for r in conn.execute(
        "SELECT name, provider, model, base_url, api_key, is_default FROM model_configs WHERE task_type='image' ORDER BY is_default DESC"
    ):
        name, provider, model, base_url, api_key, is_default = r
        dec = decrypt_secret(api_key) if api_key else ""
        print(f"name={name!r} provider={provider} model={model} default={is_default}")
        print(f"  base_url={base_url!r}")
        print(f"  key 前缀={dec[:8] if dec else '(空)'} 长度={len(dec)}")

    print("\n=== 最近失败的生成任务/资产 ===")
    for r in conn.execute(
        "SELECT a.status, a.error, t.status, t.error, t.params FROM previz_assets a "
        "LEFT JOIN generation_tasks t ON t.asset_id = a.id ORDER BY a.created_at DESC LIMIT 3"
    ):
        a_status, a_err, t_status, t_err, t_params = r
        print(f"asset_status={a_status}")
        print(f"  asset_error={a_err}")
        print(f"  task_status={t_status}")
        print(f"  task_error={t_err}")
        print(f"  task_params={t_params}")
    conn.close()


if __name__ == "__main__":
    main()
