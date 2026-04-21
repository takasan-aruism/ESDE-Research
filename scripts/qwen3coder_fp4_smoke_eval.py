#!/usr/bin/env python3
"""Small smoke/performance eval for local Qwen3-Coder FP4 OpenAI API."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request


BASE_URL = "http://127.0.0.1:8003/v1"
MODEL = "Qwen3-Coder-30B-A3B-Instruct-FP4"


TESTS = [
    {
        "name": "jp_summary",
        "max_tokens": 160,
        "messages": [
            {
                "role": "user",
                "content": (
                    "日本語で3行以内。ESDEのQwQローカルLLMをQwen3-Coderに置き換える場合、"
                    "最初に確認すべき点を箇条書きで答えて。"
                ),
            }
        ],
    },
    {
        "name": "code_generation",
        "max_tokens": 280,
        "messages": [
            {
                "role": "user",
                "content": (
                    "Write a Python function parse_metric_lines(text) that parses lines like "
                    "'loss=1.23 acc=0.98' into a list of dictionaries with float values. "
                    "Return only code."
                ),
            }
        ],
    },
    {
        "name": "bug_fix",
        "max_tokens": 320,
        "messages": [
            {
                "role": "user",
                "content": (
                    "Find the bug and provide a corrected version only:\n"
                    "def moving_average(xs, n):\n"
                    "    out = []\n"
                    "    for i in range(len(xs)):\n"
                    "        out.append(sum(xs[i-n:i]) / n)\n"
                    "    return out\n"
                ),
            }
        ],
    },
    {
        "name": "strict_json",
        "max_tokens": 180,
        "messages": [
            {
                "role": "user",
                "content": (
                    "Return only valid JSON, no markdown. Schema: "
                    "{\"ok\": boolean, \"risks\": string[], \"next\": string}. "
                    "Topic: testing a local TensorRT-LLM Qwen3-Coder FP4 server."
                ),
            }
        ],
    },
    {
        "name": "tool_call_shape",
        "max_tokens": 240,
        "messages": [
            {
                "role": "system",
                "content": "You may call tools when useful.",
            },
            {
                "role": "user",
                "content": (
                    "Use a tool call to search for files matching '*.py'. "
                    "Available function: find_files(pattern: string)."
                ),
            },
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "find_files",
                    "description": "Find files by glob pattern.",
                    "parameters": {
                        "type": "object",
                        "properties": {"pattern": {"type": "string"}},
                        "required": ["pattern"],
                    },
                },
            }
        ],
    },
]


def post_chat(payload: dict) -> tuple[float, dict]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/chat/completions",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    start = time.perf_counter()
    with urllib.request.urlopen(req, timeout=180) as resp:
        body = resp.read().decode("utf-8")
    return time.perf_counter() - start, json.loads(body)


def main() -> int:
    results = []
    for test in TESTS:
        payload = {
            "model": MODEL,
            "messages": test["messages"],
            "max_tokens": test["max_tokens"],
            "temperature": 0.2,
        }
        if "tools" in test:
            payload["tools"] = test["tools"]

        try:
            elapsed, response = post_chat(payload)
            choice = response["choices"][0]
            message = choice["message"]
            content = message.get("content") or ""
            usage = response.get("usage", {})
            completion_tokens = usage.get("completion_tokens") or 0
            tok_s = completion_tokens / elapsed if elapsed > 0 else 0.0
            item = {
                "name": test["name"],
                "elapsed_sec": round(elapsed, 3),
                "completion_tokens": completion_tokens,
                "tokens_per_sec": round(tok_s, 2),
                "finish_reason": choice.get("finish_reason"),
                "content": content,
                "tool_calls": message.get("tool_calls", []),
            }
        except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError) as exc:
            item = {"name": test["name"], "error": repr(exc)}

        results.append(item)
        print(json.dumps(item, ensure_ascii=False, indent=2))
        print()

    print("SUMMARY")
    for item in results:
        if "error" in item:
            print(f"- {item['name']}: ERROR {item['error']}")
        else:
            print(
                f"- {item['name']}: {item['elapsed_sec']}s, "
                f"{item['completion_tokens']} toks, {item['tokens_per_sec']} tok/s"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
