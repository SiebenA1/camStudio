"""诊断：查看数据库中的模型配置与 API Key 状态。"""
import sqlite3

from app.core.security import decrypt_secret


def main() -> None:
    conn = sqlite3.connect("data/realframe.db")
    rows = conn.execute(
        "SELECT id, name, provider, model, task_type, is_default, enabled, api_key "
        "FROM model_configs ORDER BY task_type, is_default DESC, updated_at DESC"
    ).fetchall()
    print("=== model_configs ===")
    for oid, name, provider, model, tt, isdef, en, apikey in rows:
        dec = decrypt_secret(apikey) if apikey else ""
        status = f"len={len(dec)}" if dec else "EMPTY"
        print(f"[{tt}] default={isdef} enabled={en} name={name!r} model={model}")
        print(f"      api_key: {status}")
    conn.close()


if __name__ == "__main__":
    main()
