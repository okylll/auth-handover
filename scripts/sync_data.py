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
DEFAULT_RULES_TARGET = Path(".agents/skills/skill-auth/references/逻辑规则.md")
DEFAULT_PAGES_TARGET = Path(".agents/skills/skill-auth/references/页面索引.md")


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
            "directory": strip_inline_markdown(fields.get("所属目录", "")),
            "type": strip_inline_markdown(fields["页面类型"]),
            "keywords": parse_keywords(fields["查询关键词"], page_id),
            "contents": parse_nested_bullets(fields["主要内容"], page_id, "主要内容", excluded),
            "status": status,
            "pixsoPosition": strip_inline_markdown(fields.get("Pixso 位置", "")),
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


def markdown_list(items: list[str], indent: str = "") -> str:
    return "\n".join(f"{indent}- {item}" for item in items)


def generate_rules_markdown(rules: list[dict[str, object]]) -> str:
    parts = [
        "# 逻辑规则",
        "",
        "本文件由 `scripts/sync_data.py` 根据允许公开的同步结果生成。",
        "只包含公开交接资料。",
        "",
        f"未命中规则时固定回答：{EMPTY_MESSAGE}",
        "",
        "## 使用原则",
        "",
        "- 只根据本文件已有 RULE 回答权限逻辑问题。",
        "- 可以组合多条已确认规则回答比较或关联问题。",
        "- 不得根据行业常识、相似功能、页面漏改文案或个人推断补充项目结论。",
        "- 用户组本身不支持限制，只支持授予和回收。",
        "- 角色只有授予和回收，没有限制。",
        "- 稿件中的“岗位”统一理解为角色下的动态模板。",
        "",
    ]

    for rule in rules:
        parts.extend([
            f"## {rule['id']} {rule['title']}",
            "",
            "**问题**",
            "",
            str(rule["question"]),
            "",
            "**结论**",
            "",
            markdown_list(rule["conclusion"]),  # type: ignore[arg-type]
            "",
        ])

        notes = rule["notes"]
        if notes:
            parts.extend([
                "**必要说明**",
                "",
                markdown_list(notes),  # type: ignore[arg-type]
                "",
            ])

        parts.extend([
            "**RULE 来源**",
            "",
            markdown_list(rule["sources"]),  # type: ignore[arg-type]
            "",
            "---",
            "",
        ])

    return "\n".join(parts).rstrip() + "\n"


def generate_pages_markdown(pages: list[dict[str, object]]) -> str:
    parts = [
        "# 页面索引",
        "",
        "本文件由 `scripts/sync_data.py` 根据允许公开的同步结果生成。",
        "只包含公开交接资料。",
        "",
        "## 使用原则",
        "",
        "- 查询流程、页面或 Pixso 位置时，优先根据页面名称、流程名称和查询关键词匹配。",
        "- 返回页面时必须给出 PAGE 来源和 Pixso 地址。",
        "- 设计稿中的“岗位”统一理解为角色下的动态模板。",
        f"- 没有匹配页面时回答：{EMPTY_MESSAGE}",
        "",
    ]

    for page in pages:
        parts.extend([
            f"## {page['id']} {page['name']}",
            "",
            f"- 页面名称：{page['name']}",
            f"- 所属目录：{page.get('directory') or '未记录'}",
            f"- 页面类型：{page['type']}",
            f"- 查询关键词：{'、'.join(page['keywords'])}",  # type: ignore[arg-type]
            "- 主要内容：",
            markdown_list(page["contents"], "  "),  # type: ignore[arg-type]
            f"- Pixso 位置：{page.get('pixsoPosition') or page['name']}",
            f"- Pixso 地址：{page['pixsoUrl']}",
            f"- 状态：{page['status']}",
            "",
            "---",
            "",
        ])

    return "\n".join(parts).rstrip() + "\n"


def write_generated_file(target: Path, output: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_target = target.with_name(target.name + ".tmp")
    tmp_target.write_text(output, encoding="utf-8")
    tmp_target.replace(target)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync public auth handover data from workskills markdown.")
    parser.add_argument("--source", required=True, help="Directory containing 逻辑规则.md and 页面索引.md")
    parser.add_argument("--target", default="data.js", help="Generated data.js path, relative to current directory by default")
    parser.add_argument("--rules-target", default=str(DEFAULT_RULES_TARGET), help="Generated public Skill 逻辑规则.md path")
    parser.add_argument("--pages-target", default=str(DEFAULT_PAGES_TARGET), help="Generated public Skill 页面索引.md path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_dir = Path(args.source).expanduser()
    data_target = Path(args.target)
    rules_target = Path(args.rules_target)
    pages_target = Path(args.pages_target)
    rules_path = source_dir / "逻辑规则.md"
    pages_path = source_dir / "页面索引.md"

    excluded: list[str] = []

    try:
        rules_text = read_text(rules_path)
        pages_text = read_text(pages_path)
        rules = parse_rules(rules_text, excluded)
        pages = parse_pages(pages_text, excluded)
        write_generated_file(data_target, generate_data_js(rules, pages))
        write_generated_file(rules_target, generate_rules_markdown(rules))
        write_generated_file(pages_target, generate_pages_markdown(pages))
    except SyncError as exc:
        print(f"同步失败：{exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"同步失败：无法写入目标文件 ({exc})", file=sys.stderr)
        return 1

    print(f"导入的规则数量：{len(rules)}")
    print(f"导入的页面数量：{len(pages)}")
    print("被排除的待确认内容：")
    if excluded:
        for item in excluded:
            print(f"- {item}")
    else:
        print("- 无")
    print("生成的目标文件：")
    for target in (data_target, rules_target, pages_target):
        print(f"- {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
