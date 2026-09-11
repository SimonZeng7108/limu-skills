# -*- coding: utf-8 -*-
"""Parse Xiaohongshu comment TXT dumps into assets/data.js."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMENTS_DIR = ROOT / "comments"
CATALOG_PATH = ROOT / "replies" / "catalog.json"
SKILLS_DIR = ROOT / "skills"
OUT_JS = ROOT / "assets" / "data.js"

TITLE_ZH = {
    "01-agent-skills": "Agent 技能",
    "02-agents": "Agent",
    "03-embodied-robotics": "具身与机器人",
    "04-research-phd": "科研与博士",
    "05-career-hiring": "职业与招聘",
    "06-infra-hardware": "基建与硬件",
    "07-learning": "学习 AI",
    "08-applied-verticals": "应用与垂类",
    "09-models-safety": "模型与安全",
    "10-misc": "其他",
}

DESC_ZH = {
    "01-agent-skills": "怎么和 Agent 协作：写代码、review、做深、扛下整块工作",
    "02-agents": "Agent 本身：harness、记忆、RSI、消费级 Agent",
    "03-embodied-robotics": "机器人、VLA、世界模型，以及 AI 能不能搞定物理世界",
    "04-research-phd": "读博、导师、学界与工业界、怎么选题",
    "05-career-hiring": "工作、实习、面试、管理岗、怎么吃饭",
    "06-infra-hardware": "训练基建、芯片、编译器、端侧",
    "07-learning": "怎么入门、非科班路径、论文精读、会不会太晚",
    "08-applied-verticals": "行业应用、创业、推荐、医疗、翻译、SFT、AI4S",
    "09-models-safety": "多模态、微调、LLM 方向、对齐与安全",
    "10-misc": "段子、学区房、担责，以及其他不好归类的",
}

SKILL_FOLDERS = {
    "01-agent-skills": "limu-agent-skills",
    "02-agents": "limu-agents",
    "03-embodied-robotics": "limu-embodied-robotics",
    "04-research-phd": "limu-research-phd",
    "05-career-hiring": "limu-career-hiring",
    "06-infra-hardware": "limu-infra-hardware",
    "07-learning": "limu-learning-ai",
    "08-applied-verticals": "limu-applied-verticals",
    "09-models-safety": "limu-models-safety",
    "10-misc": "limu-misc",
}

TIME_RE = re.compile(
    r"^时间:\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})(?:\s*·\s*(.+))?$"
)
AUTHOR_MARK = "[作者]"


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    raw, body = parts[1], parts[2].lstrip("\n")
    meta: dict[str, str] = {}
    key = None
    chunks: list[str] = []
    for line in raw.splitlines():
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if match and not line.startswith(" "):
            if key:
                meta[key] = " ".join(chunks).strip()
            key = match.group(1)
            rest = match.group(2).strip()
            chunks = [] if rest in (">", ">-", "|", "|-") else [rest]
        elif key and (line.startswith("  ") or line.startswith("\t")):
            chunks.append(line.strip())
    if key:
        meta[key] = " ".join(chunks).strip()
    return meta, body


def load_skills() -> list[dict]:
    skills = []
    for cat_id, folder in SKILL_FOLDERS.items():
        path = SKILLS_DIR / folder / "SKILL.md"
        if not path.exists():
            continue
        meta, body = parse_frontmatter(path.read_text(encoding="utf-8-sig"))
        heading = next(
            (line[2:].strip() for line in body.splitlines() if line.startswith("# ")),
            TITLE_ZH.get(cat_id, folder),
        )
        skills.append(
            {
                "id": meta.get("name") or folder,
                "categoryId": cat_id,
                "folder": folder,
                "title": heading,
                "titleZh": TITLE_ZH.get(cat_id, heading),
                "description": meta.get("description") or DESC_ZH.get(cat_id, ""),
                "body": body.strip(),
                "path": f"skills/{folder}/SKILL.md",
            }
        )
    return skills


def parse_comment(block: str) -> dict | None:
    raw_lines = [line.rstrip() for line in block.split("\n")]
    while raw_lines and raw_lines[0] == "":
        raw_lines.pop(0)
    while raw_lines and raw_lines[-1] == "":
        raw_lines.pop()
    if len(raw_lines) < 1:
        return None

    time_idx = next(
        (i for i, line in enumerate(raw_lines) if line.startswith("时间:")),
        None,
    )
    if time_idx is None:
        return None

    if time_idx == 0:
        name_raw = "匿名"
        is_author = False
        name = "匿名"
    else:
        name_raw = "\n".join(raw_lines[:time_idx]).strip()
        is_author = AUTHOR_MARK in name_raw or name_raw.strip() == "李沐"
        name = name_raw.replace(AUTHOR_MARK, "").strip() or "匿名"

    match = TIME_RE.match(raw_lines[time_idx])
    if not match:
        return None

    rest = raw_lines[time_idx + 1 :]
    reply_to = None
    if rest and rest[0].startswith("回复:"):
        reply_to = rest[0].split(":", 1)[1].strip()
        if reply_to.startswith("@"):
            reply_to = reply_to[1:]
        rest = rest[1:]

    content = "\n".join(rest).strip()
    return {
        "name": name,
        "isAuthor": is_author,
        "datetime": match.group(1),
        "location": (match.group(2) or "").strip(),
        "replyTo": reply_to,
        "content": content,
    }


def parse_file(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")

    dialog_id = None
    comment_id = None
    body_start = 0
    for i, line in enumerate(lines):
        if line.startswith("对话"):
            dialog_id = line.replace("对话", "").strip()
        elif line.startswith("评论ID:"):
            comment_id = line.split(":", 1)[1].strip()
            body_start = i + 1
            break

    body = "\n".join(lines[body_start:]).strip()
    if not body:
        return None

    if "--- 回复 ---" in body:
        root_part, replies_part = body.split("--- 回复 ---", 1)
    else:
        root_part, replies_part = body, ""

    root = parse_comment(root_part)
    if not root:
        return None

    replies = []
    for block in re.split(r"\n\s*\n", replies_part.strip()):
        if not block.strip():
            continue
        comment = parse_comment(block)
        if comment:
            replies.append(comment)

    author_replies = [item for item in replies if item["isAuthor"]]
    return {
        "file": path.name,
        "dialogId": dialog_id,
        "commentId": comment_id,
        "root": root,
        "replies": replies,
        "hasAuthorReply": bool(author_replies),
        "authorReplyCount": len(author_replies),
        "replyCount": len(replies),
    }


def main() -> None:
    files = sorted(COMMENTS_DIR.glob("*.txt"))
    parsed = []
    skipped = []
    for path in files:
        try:
            thread = parse_file(path)
        except Exception as exc:  # noqa: BLE001
            skipped.append((path.name, str(exc)))
            continue
        if thread is None:
            skipped.append((path.name, "parse failed"))
            continue
        parsed.append(thread)

    author_threads = [t for t in parsed if t["hasAuthorReply"]]
    author_threads.sort(key=lambda t: (t["root"]["datetime"], t["dialogId"] or ""))

    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    dialog_to_cat = {}
    categories = []
    for cat in catalog.get("categories", []):
        cat_id = cat["id"]
        categories.append(
            {
                "id": cat_id,
                "title": cat.get("title") or cat_id,
                "titleZh": TITLE_ZH.get(cat_id, cat.get("title") or cat_id),
                "description": DESC_ZH.get(cat_id, cat.get("description") or ""),
                "count": cat.get("count") or len(cat.get("threads") or []),
            }
        )
        for item in cat.get("threads") or []:
            dialog_id = item.get("dialogId")
            if dialog_id:
                dialog_to_cat[dialog_id] = cat_id

    skills = load_skills()
    skill_by_cat = {item["categoryId"]: item["id"] for item in skills}
    for cat in categories:
        cat["skillId"] = skill_by_cat.get(cat["id"])

    for thread in author_threads:
        thread["categoryId"] = dialog_to_cat.get(thread["dialogId"] or "", "10-misc")

    all_comments = sum(1 + t["replyCount"] for t in parsed)
    shown_comments = sum(1 + t["replyCount"] for t in author_threads)
    # Xiaohongshu shows 共 1898 条评论 on the note; saved files are a subset
    # (deleted/hidden comments and a few unexpanded replies).
    official_all_comments = 1898

    payload = {
        "sourceNote": {
            "author": "李沐",
            "badge": "作者",
            "location": "美国",
            "posted": "2026-09-08",
            "title": "Ask Me Anything",
            "url": "https://www.xiaohongshu.com/explore/6a9f7b27000000000f039800?xsec_token=ABlD0QZda9uE7KqikfwwusafTHZlpkGIsUGMZD5FzImCE=&xsec_source=pc_search",
            "content": (
                "大家好，我是李沐。BosonAI联创，前Amazon AI Sr. Principal Scientist。"
                " AI越来越强，今天应该学什么，才能不被AI淘汰？人还需要学编程吗？"
                "大学生今天应该学什么？AI会让哪些能力变得更重要，而不是更不重要？"
                "未来最值得培养的能力是什么？创业者真正需要懂多少AI技术？"
                " 欢迎大家尽情给我提问！Ask Me Anything！"
            ),
            "tags": ["小红书科技AMA", "李沐"],
        },
        "stats": {
            "totalFiles": len(files),
            "parsedThreads": len(parsed),
            "authorThreads": len(author_threads),
            "authorReplies": sum(t["authorReplyCount"] for t in author_threads),
            "mainComments": len(parsed),
            "allComments": official_all_comments,
            "savedComments": all_comments,
            "shownComments": shown_comments,
            "updatedAt": date.today().isoformat(),
        },
        "categories": categories,
        "skills": skills,
        "threads": author_threads,
    }

    OUT_JS.parent.mkdir(parents=True, exist_ok=True)
    json_text = json.dumps(payload, ensure_ascii=False, indent=2)
    OUT_JS.write_text(
        "window.XHS_DATA = " + json_text + ";\n",
        encoding="utf-8",
    )

    print(f"files: {len(files)}")
    print(f"parsed: {len(parsed)}")
    print(f"author-replied threads: {len(author_threads)}")
    print(f"author replies: {payload['stats']['authorReplies']}")
    print(f"main comments: {payload['stats']['mainComments']}")
    print(f"all comments: {payload['stats']['allComments']}")
    print(f"comments shown: {payload['stats']['shownComments']}")
    print(f"updated: {payload['stats']['updatedAt']}")
    print(f"categories: {len(categories)}")
    print(f"skills: {len(skills)}")
    if skipped:
        print("skipped:")
        for name, reason in skipped:
            print(f"  {name}: {reason}")
    empty_author = [t["file"] for t in parsed if t["hasAuthorReply"] and not t["root"]["content"]]
    if empty_author:
        print("empty roots:", empty_author)


if __name__ == "__main__":
    main()
