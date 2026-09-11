"""从模型输出中稳健地提取 JSON 对象。

模型常会在 JSON 之后追加说明文字、或多个 JSON、或 markdown 代码块，
因此用「花括号配对」提取第一个完整 JSON 对象，而非贪婪正则。
"""
from __future__ import annotations

import json
import re

from app.core.errors import AppError


def extract_json_object(text: str) -> dict:
    text = (text or "").strip()
    # 去掉 markdown 代码块围栏（```json ... ```）
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text).strip()

    start = text.find("{")
    if start == -1:
        raise AppError(502, "parse_failed", "模型返回中未找到 JSON 对象")

    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        c = text[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except json.JSONDecodeError as e:
                        raise AppError(502, "parse_failed", f"模型返回 JSON 无法解析：{e}") from e
    raise AppError(502, "parse_failed", "模型返回 JSON 不完整（花括号未闭合）")
