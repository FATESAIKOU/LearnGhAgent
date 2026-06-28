#!/usr/bin/env python3
"""
chatlog.py — 維護對話陣列的工具。

用法：
  chatlog.py <json-file> init
  chatlog.py <json-file> append <role> <text>
  chatlog.py <json-file> append-file <role> <file>
  chatlog.py <json-file> append-round <round> <role> <text>
  chatlog.py <json-file> append-round-file <round> <role> <file>
  chatlog.py <json-file> load-context-from-pr-log [review_comments.json]
        從 stdin 讀 gh pr view --json body,comments,reviews 輸出。
        可選參數: review_comments.json (gh api /pulls/N/comments 輸出)。
  chatlog.py <json-file> toprompt
  chatlog.py <json-file> toprompt-from-round <round>
  chatlog.py <json-file> len / get <idx> / clear / rounds
"""
import json
import os
import re
import sys
from pathlib import Path

TAG_RE = re.compile(r"<!-- chatlog:(\w+):(\w+) -->")


def is_bot(login: str) -> bool:
    return ("bot" in login or login.startswith("github-actions")
            or login.startswith("app/") or "[bot]" in login)


def parse_tag(body: str) -> tuple[str | None, str | None]:
    m = TAG_RE.search(body)
    return (m.group(1), m.group(2)) if m else (None, None)


def strip_tag(body: str) -> str:
    return TAG_RE.sub("", body, count=1).lstrip("\n")


def load(path: str) -> dict:
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"messages": []}


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
    cur = None
    for m in data["messages"]:
        r = m.get("round")
        if from_round and r == from_round:
            started = True
        if not started:
            continue
        if r and r != cur:
            cur = r
            lines.append(f"=== Round {r} ===")
        lines.append(f"[{m['role'].capitalize()}]:")
        lines.append(m["content"])
        lines.append("")
    return "\n".join(lines).strip()


def _time(obj: dict) -> str:
    return obj.get("createdAt") or obj.get("created_at") or obj.get("submittedAt") or obj.get("submitted_at") or ""


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__, file=sys.stderr)
        return 2

    path, cmd, *args = sys.argv[1], sys.argv[2], sys.argv[3:]
    data = load(path)

    if cmd == "init":
        save(path, {"messages": []})
        print(f"initialized: {path}")

    elif cmd == "append":
        if len(args) < 2: return 2
        append_msg(data, args[0], args[1])
        save(path, data)

    elif cmd == "append-file":
        if len(args) < 2: return 2
        append_msg(data, args[0], Path(args[1]).read_text(encoding="utf-8"))
        save(path, data)

    elif cmd == "append-round":
        if len(args) < 3: return 2
        append_msg(data, args[1], args[2], round_id=args[0])
        save(path, data)

    elif cmd == "append-round-file":
        if len(args) < 3: return 2
        append_msg(data, args[1], Path(args[2]).read_text(encoding="utf-8"), round_id=args[0])
        save(path, data)

    elif cmd == "load-context-from-pr-log":
        gh_data = json.load(sys.stdin)
        data = {"messages": []}

        # 可選: review_comments file
        rc_by_review: dict[int, list[dict]] = {}
        if args:
            rc_list = json.loads(Path(args[0]).read_text(encoding="utf-8"))
            for rc in rc_list:
                rid = rc.get("pull_request_review_id")
                if rid:
                    rc_by_review.setdefault(rid, []).append(rc)

        # comments → summaries + user messages
        summaries: dict[str, str] = {}
        user_msgs: list[dict] = []
        for c in gh_data.get("comments", []):
            login = c.get("author", {}).get("login", "")
            body = c.get("body", "")
            tag_type, tag_round = parse_tag(body)
            if tag_type == "summary" and tag_round:
                summaries[tag_round] = strip_tag(body)
            elif not is_bot(login):
                user_msgs.append({"body": body, "time": _time(c)})

        # reviews → user messages (body + file comments 合併)
        for r in gh_data.get("reviews", []):
            login = r.get("author", {}).get("login", "")
            rbody = (r.get("body") or "").strip()
            if is_bot(login) or r.get("state") != "COMMENTED":
                continue
            parts = [rbody] if rbody else []
            for fc in rc_by_review.get(r.get("id"), []):
                fc_login = fc.get("user", {}).get("login", "")
                if is_bot(fc_login):
                    continue
                parts.append(f"[file:{fc.get('path','')}:{fc.get('line','')}] {fc.get('body','')}")
            if parts:
                user_msgs.append({"body": "\n\n".join(parts), "time": _time(r)})

        user_msgs.sort(key=lambda m: m["time"])
        user_texts = [m["body"] for m in user_msgs]

        current_num = 1 + len(user_texts)
        current_round = f"R{current_num}"

        # R1: PR body
        append_msg(data, "user", gh_data.get("body", ""), round_id="R1")
        if current_num > 1 and "R1" in summaries:
            append_msg(data, "assistant", summaries["R1"], round_id="R1")

        # R2..current-1
        for i, uc in enumerate(user_texts):
            rn = i + 2
            if rn >= current_num: break
            rid = f"R{rn}"
            append_msg(data, "user", uc, round_id=rid)
            if rid in summaries:
                append_msg(data, "assistant", summaries[rid], round_id=rid)

        # current round: user only
        if current_num > 1:
            ci = current_num - 2
            if 0 <= ci < len(user_texts):
                append_msg(data, "user", user_texts[ci], round_id=current_round)

        save(path, data)
        print(f"loaded-context-from-pr-log: {len(data['messages'])} messages, current round {current_round}, summaries found: {list(summaries.keys())}")
        gh_out = Path(os.environ.get("GITHUB_OUTPUT", "/dev/null"))
        with open(gh_out, "a", encoding="utf-8") as f:
            f.write(f"round_id={current_round}\n")

    elif cmd == "toprompt":
        print(to_prompt(data))

    elif cmd == "toprompt-from-round":
        if len(args) < 1: return 2
        print(to_prompt(data, from_round=args[0]))

    elif cmd == "len":
        print(len(data["messages"]))

    elif cmd == "get":
        if len(args) < 1: return 2
        idx = int(args[0])
        if 0 <= idx < len(data["messages"]):
            print(json.dumps(data["messages"][idx], ensure_ascii=False, indent=2))
        else:
            print(f"index out of range: {idx}", file=sys.stderr)
            return 1

    elif cmd == "clear":
        save(path, {"messages": []})
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
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
