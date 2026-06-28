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
  chatlog.py <json-file> load-context-from-pr-log            從 stdin 讀 gh pr view --json body,comments，建對話並計算 round id
  chatlog.py <json-file> toprompt                          轉成 prompt 字串（交替 user/assistant）
  chatlog.py <json-file> toprompt-from-round <round>       只含指定 round 起（含）的訊息
  chatlog.py <json-file> len                               回傳 message 數
  chatlog.py <json-file> get <index>                       取第 N 則
  chatlog.py <json-file> clear                             清空
  chatlog.py <json-file> rounds                            列出所有 round

load-context-from-pr-log 的 stdin 格式（gh pr view --json body,comments,reviews 原始輸出）：
{
  "body": "PR body 原文",
  "comments": [
    {"author": {"login": "..."}, "body": "<!-- chatlog:summary:R1 -->...", "createdAt": "..."},
    {"author": {"login": "FATESAIKOU"}, "body": "user comment", "createdAt": "..."},
    ...
  ],
  "reviews": [
    {"author": {"login": "FATESAIKOU"}, "body": "NG\n請修正", "state": "COMMENTED", "submittedAt": "..."},
    ...
  ]
}

bot comment 透過 body 內的 <!-- chatlog:summary:R1 --> HTML comment tag 標記為 summary。
chatlog.py 會：過濾 bot comments/reviews、用 tag 識別 summary、按 createdAt/submittedAt 排序 user 訊息、
配對 user/assistant 交替、current round 只加 user 不加 assistant。
"""
import json
import os
import re
import sys
from pathlib import Path


TAG_RE = re.compile(r"<!-- chatlog:(\w+):(\w+) -->")


def is_bot(login: str) -> bool:
    return (
        "bot" in login
        or login.startswith("github-actions")
        or login.startswith("app/")
        or "[bot]" in login
    )


def parse_tag(body: str) -> tuple[str | None, str | None]:
    m = TAG_RE.search(body)
    if m:
        return m.group(1), m.group(2)
    return None, None


def strip_tag(body: str) -> str:
    return TAG_RE.sub("", body, count=1).lstrip("\n")


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

    elif cmd == "load-context-from-pr-log":
        gh_data = json.load(sys.stdin)
        data = {"messages": []}

        # 從 comments 抓 summaries（bot comment 含 <!-- chatlog:summary:Rn --> tag）
        # 與 user comments（非 bot author），按 createdAt 排序
        comments = gh_data.get("comments", [])
        summaries: dict[str, str] = {}
        user_messages: list[dict] = []
        for c in comments:
            login = c.get("author", {}).get("login", "")
            cbody = c.get("body", "")
            created = c.get("createdAt", "")
            tag_type, tag_round = parse_tag(cbody)
            if tag_type == "summary" and tag_round:
                summaries[tag_round] = strip_tag(cbody)
            elif not is_bot(login):
                user_messages.append({"body": cbody, "createdAt": created})

        # 也從 reviews 抓 user 訊息（PR review comment，非一般 comment）
        reviews = gh_data.get("reviews", [])
        for r in reviews:
            login = r.get("author", {}).get("login", "")
            rbody = r.get("body", "")
            submitted = r.get("submittedAt", "")
            state = r.get("state", "")
            if not is_bot(login) and rbody.strip() and state == "COMMENTED":
                user_messages.append({"body": rbody, "createdAt": submitted})

        user_messages.sort(key=lambda c: c["createdAt"])
        user_texts = [c["body"] for c in user_messages]

        # round id = PR body 算第 1 次 + user comments 數
        current_num = 1 + len(user_texts)
        current_round = f"R{current_num}"

        # R1: [User] = PR body
        body = gh_data.get("body", "")
        append_msg(data, "user", body, round_id="R1")

        # R1: [Assistant] = summaries["R1"]（若存在且 R1 不是 current）
        if current_num > 1:
            r1_sum = summaries.get("R1")
            if r1_sum:
                append_msg(data, "assistant", r1_sum, round_id="R1")

        # R2..current-1: [User] + [Assistant]
        for i, uc in enumerate(user_texts):
            round_num = i + 2
            if round_num >= current_num:
                break
            rid = f"R{round_num}"
            append_msg(data, "user", uc, round_id=rid)
            summ = summaries.get(rid)
            if summ:
                append_msg(data, "assistant", summ, round_id=rid)

        # Current round: 只 [User]（若 current round 不是 R1）
        if current_num > 1:
            current_idx = current_num - 2
            if 0 <= current_idx < len(user_texts):
                append_msg(data, "user", user_texts[current_idx], round_id=current_round)

        save(path, data)
        print(f"loaded-context-from-pr-log: {len(data['messages'])} messages, current round {current_round}, summaries found: {list(summaries.keys())}")
        # GITHUB_OUTPUT for workflow
        gh_out = Path(os.environ.get("GITHUB_OUTPUT", "/dev/null"))
        with open(gh_out, "a", encoding="utf-8") as f:
            f.write(f"round_id={current_round}\n")

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