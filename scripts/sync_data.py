#!/usr/bin/env python3
"""Sync public handover data from the canonical workskills markdown files."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


EMPTY_MESSAGE = "现有交接资料中没有相关记录，无法根据已有规则判断。"
PENDING_MARKERS = ("待确认", "二次授权", "尚未最终确认")


class SyncError(Exception):
    """Raised when source markdown cannot be safely converted."""


def read_text(path: Path) -> str:
    try:
      return path.read_text(encoding="utf-8")
    except OSError as exc:
      raise SyncError(f"无法读取源文件：{path}") from exc


def is_pending_fragment(text: str) -> bool:
    return any(marker in text for marker in PENDING_MARKERS)


def strip_inline_markdown(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", text)
    text = text.replace("**", "")
    return text.strip()


def split_sentences(text: str) -> list[str]:
    parts = re.findall(r"[^。！？；]+[。！？；]?", text)
    return [part.strip() for part in parts if part.strip()]


def add_public_text(text: str, items: list[str], section_id: str, excluded: list[str]) -> None:
    text = strip_inline_markdown(text)
    if not text:
        return

    if not is_pending_fragment(text):
        items.append(text)
        return

    kept_parts = []
    for sentence in split_sentences(text):
        if is_pending_fragment(sentence):
            excluded.append(f"{section_id}: {sentence}")
        elif sentence:
            kept_parts.append(sentence)

    kept = "".join(kept_parts).strip()
    if kept:
        items.append(kept)


def split_numbered_sections(text: str, prefix: str) -> list[tuple[str, str, str]]:
    pattern = re.compile(rf"^##\s+({prefix}-\d{{3}})\s+(.+?)\s*$", re.MULTILINE)
    matches = list(pattern.finditer(text))
    if not matches:
        raise SyncError(f"没有找到 {prefix} 区块")

    sections = []
    for index, match in enumerate(matches):
        next_start = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections.append((match.group(1), match.group(2).strip(), text[match.end():next_start]))
    return sections


def extract_bold_blocks(body: str, section_id: str) -> dict[str, str]:
    pattern = re.compile(r"^\*\*(.+?)\*\*\s*$", re.MULTILINE)
    matches = list(pattern.finditer(body))
    blocks: dict[str, str] = {}

    for index, match in enumerate(matches):
        label = match.group(1).strip()
        next_start = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        blocks[label] = body[match.end():next_start].strip()

    if not blocks:
        raise SyncError(f"{section_id} 缺少加粗字段标题")
    return blocks


def flush_paragraph(parts: list[str], items: list[str], section_id: str, excluded: list[str]) -> None:
    if not parts:
        return
    text = strip_inline_markdown("".join(parts))
    parts.clear()
    add_public_text(text, items, section_id, excluded)


def parse_content_items(raw: str, section_id: str, excluded: list[str]) -> list[str]:
    items: list[str] = []
    paragraph: list[str] = []

    for original_line in raw.splitlines():
        line = original_line.strip()
        if not line:
            flush_paragraph(paragraph, items, section_id, excluded)
            continue

        bullet = re.match(r"^(?:[-*+]|\d+\.)\s+(.+)$", line)
        quote = re.match(r"^>\s*(.+)$", line)

        if bullet:
            flush_paragraph(paragraph, items, section_id, excluded)
            add_public_text(bullet.group(1), items, section_id, excluded)
        elif quote:
            flush_paragraph(paragraph, items, section_id, excluded)
            add_public_text(quote.group(1), items, section_id, excluded)
        else:
            paragraph.append(strip_inline_markdown(line))

    flush_paragraph(paragraph, items, section_id, excluded)
    return items


def parse_sources(raw: str, section_id: str) -> list[str]:
    sources = []
    for line in raw.splitlines():
        stripped = line.strip()
        match = re.match(r"^(?:[-*+]|\d+\.)\s+(.+)$", stripped)
        if match:
            source = strip_inline_markdown(match.group(1))
            if source:
                sources.append(source)

    if not sources:
        raise SyncError(f"{section_id} 缺少来源页面")
    return sources


def parse_rules(text: str, excluded: list[str]) -> list[dict[str, object]]:
    rules = []

    for rule_id, title, body in split_numbered_sections(text, "RULE"):
        if is_pending_fragment(title):
            excluded.append(f"{rule_id}: {title}")
            continue

        blocks = extract_bold_blocks(body, rule_id)
        required = ("问题", "结论", "来源")
        missing = [label for label in required if label not in blocks]
        if missing:
            raise SyncError(f"{rule_id} 缺少字段：{', '.join(missing)}")

        question_items = parse_content_items(blocks["问题"], rule_id, excluded)
        conclusion = parse_content_items(blocks["结论"], rule_id, excluded)
        notes = parse_content_items(blocks.get("说明", ""), rule_id, excluded)
        sources = parse_sources(blocks["来源"], rule_id)

        if len(question_items) != 1:
            raise SyncError(f"{rule_id} 的问题字段应解析为 1 条，实际为 {len(question_items)} 条")
        if not conclusion:
            raise SyncError(f"{rule_id} 的结论在过滤后为空")

        rules.append({
            "id": rule_id,
            "title": strip_inline_markdown(title),
            "question": question_items[0],
            "conclusion": conclusion,
            "notes": notes,
            "sources": sources,
        })

    if not rules:
        raise SyncError("没有导入任何 RULE")
    return rules


def parse_top_level_fields(body: str, page_id: str) -> dict[str, str]:
    fields: dict[str, list[str]] = {}
    current: str | None = None

    for line in body.splitlines():
        if line.strip() == "---":
            continue

        match = re.match(r"^\*\s*([^：:]+)[：:]\s*(.*)$", line)
        if match:
            current = match.group(1).strip()
            fields[current] = [match.group(2).strip()]
            continue

        if current:
            fields[current].append(line.rstrip())

    if not fields:
        raise SyncError(f"{page_id} 缺少页面字段")
    return {key: "\n".join(value).strip() for key, value in fields.items()}


def parse_keywords(raw: str, page_id: str) -> list[str]:
    keywords = [part.strip() for part in re.split(r"[、,，]", raw) if part.strip()]
    if not keywords:
        raise SyncError(f"{page_id} 缺少查询关键词")
    return keywords


def parse_nested_bullets(raw: str, page_id: str, field_name: str, excluded: list[str]) -> list[str]:
    items = []
    for line in raw.splitlines():
        stripped = line.strip()
        match = re.match(r"^(?:[-*+]|\d+\.)\s+(.+)$", stripped)
        if not match:
            continue
        add_public_text(match.group(1), items, f"{page_id} {field_name}", excluded)

    if not items:
        raise SyncError(f"{page_id} 的{field_name}为空或无法解析")
    return items


def parse_pixso_url(raw: str, page_id: str) -> str:
    match = re.search(r"\((https?://[^)]+)\)", raw)
    if not match:
        match = re.search(r"https?://\S+", raw)
    if not match:
        raise SyncError(f"{page_id} 缺少 Pixso 地址")
    return match.group(1 if match.lastindex else 0).rstrip(")")


def parse_pages(text: str, excluded: list[str]) -> list[dict[str, object]]:
    pages = []

    for page_id, title, body in split_numbered_sections(text, "PAGE"):
        if is_pending_fragment(title):
            excluded.append(f"{page_id}: {title}")
            continue

        fields = parse_top_level_fields(body, page_id)
        required = ("页面名称", "页面类型", "查询关键词", "主要内容", "Pixso 地址", "状态")
        missing = [field for field in required if field not in fields or not fields[field].strip()]
        if missing:
            raise SyncError(f"{page_id} 缺少字段：{', '.join(missing)}")

        status = strip_inline_markdown(fields["状态"])
        if is_pending_fragment(status):
            excluded.append(f"{page_id} 状态: {status}")
            continue

        pages.append({
            "id": page_id,
            "name": strip_inline_markdown(fields["页面名称"]),
            "type": strip_inline_markdown(fields["页面类型"]),
            "keywords": parse_keywords(fields["查询关键词"], page_id),
            "contents": parse_nested_bullets(fields["主要内容"], page_id, "主要内容", excluded),
            "status": status,
            "pixsoUrl": parse_pixso_url(fields["Pixso 地址"], page_id),
        })

    if not pages:
        raise SyncError("没有导入任何 PAGE")
    return pages


def generate_data_js(rules: list[dict[str, object]], pages: list[dict[str, object]]) -> str:
    payload = {
        "rules": rules,
        "pages": pages,
        "emptyMessage": EMPTY_MESSAGE,
    }
    json_payload = json.dumps(payload, ensure_ascii=False, indent=2)
    return (
        "// This file is generated by scripts/sync_data.py. Do not edit manually.\n"
        f"window.AUTH_HANDOVER_DATA = {json_payload};\n"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync public auth handover data from workskills markdown.")
    parser.add_argument("--source", required=True, help="Directory containing 逻辑规则.md and 页面索引.md")
    parser.add_argument("--target", default="data.js", help="Generated data.js path, relative to current directory by default")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_dir = Path(args.source).expanduser()
    target = Path(args.target)
    rules_path = source_dir / "逻辑规则.md"
    pages_path = source_dir / "页面索引.md"

    excluded: list[str] = []

    try:
        rules_text = read_text(rules_path)
        pages_text = read_text(pages_path)
        rules = parse_rules(rules_text, excluded)
        pages = parse_pages(pages_text, excluded)
        output = generate_data_js(rules, pages)
        tmp_target = target.with_name(target.name + ".tmp")
        tmp_target.write_text(output, encoding="utf-8")
        tmp_target.replace(target)
    except SyncError as exc:
        print(f"同步失败：{exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"同步失败：无法写入目标文件：{target} ({exc})", file=sys.stderr)
        return 1

    print(f"导入的规则数量：{len(rules)}")
    print(f"导入的页面数量：{len(pages)}")
    print("被排除的待确认内容：")
    if excluded:
        for item in excluded:
            print(f"- {item}")
    else:
        print("- 无")
    print(f"生成的目标文件：{target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
