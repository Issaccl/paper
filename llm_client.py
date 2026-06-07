import json
import re
import requests

DEFAULT_BASE_URL = "https://token-plan-cn.xiaomimimo.com/v1"


def _extract_json(text):
    """从可能包含额外文字的响应中提取 JSON"""
    # 直接尝试解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # 找最外层的 [ ... ] 或 { ... }
    for start_ch, end_ch in [('[', ']'), ('{', '}')]:
        start = text.find(start_ch)
        end = text.rfind(end_ch)
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError(f"无法从响应中提取 JSON:\n{text[:500]}")


def call_llm(api_key, user_instruction, system_prompt, paragraphs,
             base_url=DEFAULT_BASE_URL, model="mimo-v2.5",
             temperature=0.1):
    user_msg = (
        "## 文档内容\n"
        f"{json.dumps(paragraphs, ensure_ascii=False, indent=2)}\n\n"
        "## 用户指令\n"
        f"{user_instruction}"
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ],
        "temperature": temperature,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    url = f"{base_url.rstrip('/')}/chat/completions"

    last_err = None
    for _ in range(2):
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=120)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            result = _extract_json(content)
            if isinstance(result, list):
                return result
            if isinstance(result, dict):
                for v in result.values():
                    if isinstance(v, list):
                        return v
            return result
        except Exception as e:
            last_err = e
    raise RuntimeError(f"API 调用失败: {last_err}")
