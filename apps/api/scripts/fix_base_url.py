"""修正 image 模型配置的 base_url（去掉错误的 /compatible-model/v1 路径）。"""
import sqlite3


def main() -> None:
    conn = sqlite3.connect("data/realframe.db")
    cur = conn.execute(
        "SELECT id, name, base_url FROM model_configs WHERE task_type='image'"
    )
    for oid, name, base_url in cur.fetchall():
        if base_url and base_url.rstrip("/") != "https://dashscope.aliyuncs.com":
            conn.execute(
                "UPDATE model_configs SET base_url='https://dashscope.aliyuncs.com' WHERE id=?",
                (oid,),
            )
            print(f"已修正: {name!r} base_url -> https://dashscope.aliyuncs.com")
    conn.commit()
    print("\n=== 修正后 image 配置 ===")
    for r in conn.execute(
        "SELECT name, model, base_url, is_default FROM model_configs WHERE task_type='image'"
    ):
        print(r)
    conn.close()


if __name__ == "__main__":
    main()
