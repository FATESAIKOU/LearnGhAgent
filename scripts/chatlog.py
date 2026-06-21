#!/usr/bin/env python3
"""
chatlog.py — 維護對話陣列的工具，支援基本陣列指令。

對話格式（JSON）：
{
  "messages": [
    {"role": "user", "content": "...", "round": "R1"},
    {"role": "assistant", "content": "...", "round": "R1"},
    ...
  ]
}

用法：
  chatlog.py <json-file> init                              初始化空對話
  chatlog.py <json-file> append <role> <text>              append 一則 message（round 可選）
  chatlog.py <json-file> append-file <role> <file>         從檔案讀內容 append
  chatlog.py <json-file> append-round <round> <role> <text>  帶 round 標記 append
  chatlog.py <json-file> append-round-file <round> <role> <file>  帶 round + 檔案內容
  chatlog.py <json-file> toprompt                          轉成 prompt 字串（交替 user/assistant）
  chatlog.py <json-file> toprompt-from-round <round>       只含指定 round 起（含）的訊息
  chatlog.py <json-file> len                               回傳 message 數
  chatlog.py <json-file> get <index>                       取第 N 則
  chatlog.py <json-file> clear                             清空
  chatlog.py <json-file> rounds                            列出所有 round
"""
import json
import sys
from pathlib import Path


def load(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {"messages": []}
    return json.loads(p.read_text(encoding="utf-8"))


def save(path: str, data: dict) -> None:
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def append_msg(data: dict, role: str, content: str, round_id: str | None = None) -> None:
    msg = {"role": role, "content": content}
    if round_id:
        msg["round"] = round_id
    data["messages"].append(msg)


def to_prompt(data: dict, from_round: str | None = None) -> str:
    lines = []
    started = from_round is None
    current_round = None
    for m in data["messages"]:
        r = m.get("round")
        if from_round and r == from_round:
            started = True
        if not started:
            continue
        if r and r != current_round:
            current_round = r
            lines.append(f"=== Round {r} ===")
        lines.append(f"[{m['role'].capitalize()}]:")
        lines.append(m["content"])
        lines.append("")
    return "\n".join(lines).strip()


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__, file=sys.stderr)
        return 2

    path = sys.argv[1]
    cmd = sys.argv[2]
    args = sys.argv[3:]
    data = load(path)

    if cmd == "init":
        data = {"messages": []}
        save(path, data)
        print(f"initialized: {path}")

    elif cmd == "append":
        if len(args) < 2:
            print("usage: append <role> <text>", file=sys.stderr)
            return 2
        append_msg(data, args[0], args[1])
        save(path, data)
        print(f"appended ({args[0]}): {len(data['messages'])} total")

    elif cmd == "append-file":
        if len(args) < 2:
            print("usage: append-file <role> <file>", file=sys.stderr)
            return 2
        content = Path(args[1]).read_text(encoding="utf-8")
        append_msg(data, args[0], content)
        save(path, data)
        print(f"appended-file ({args[0]}): {len(data['messages'])} total")

    elif cmd == "append-round":
        if len(args) < 3:
            print("usage: append-round <round> <role> <text>", file=sys.stderr)
            return 2
        append_msg(data, args[1], args[2], round_id=args[0])
        save(path, data)
        print(f"appended-round {args[0]} ({args[1]}): {len(data['messages'])} total")

    elif cmd == "append-round-file":
        if len(args) < 3:
            print("usage: append-round-file <round> <role> <file>", file=sys.stderr)
            return 2
        content = Path(args[2]).read_text(encoding="utf-8")
        append_msg(data, args[1], content, round_id=args[0])
        save(path, data)
        print(f"appended-round-file {args[0]} ({args[1]}): {len(data['messages'])} total")

    elif cmd == "toprompt":
        print(to_prompt(data))

    elif cmd == "toprompt-from-round":
        if len(args) < 1:
            print("usage: toprompt-from-round <round>", file=sys.stderr)
            return 2
        print(to_prompt(data, from_round=args[0]))

    elif cmd == "len":
        print(len(data["messages"]))

    elif cmd == "get":
        if len(args) < 1:
            print("usage: get <index>", file=sys.stderr)
            return 2
        idx = int(args[0])
        if 0 <= idx < len(data["messages"]):
            print(json.dumps(data["messages"][idx], ensure_ascii=False, indent=2))
        else:
            print(f"index out of range: {idx}", file=sys.stderr)
            return 1

    elif cmd == "clear":
        data = {"messages": []}
        save(path, data)
        print(f"cleared: {path}")

    elif cmd == "rounds":
        seen = []
        for m in data["messages"]:
            r = m.get("round")
            if r and r not in seen:
                seen.append(r)
        print(" ".join(seen) if seen else "(no rounds)")

    else:
        print(f"unknown command: {cmd}", file=sys.stderr)
        print(__doc__, file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())