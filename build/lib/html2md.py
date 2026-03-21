#!/usr/bin/env python3

import argparse
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup
from bs4.element import Tag
from html_to_markdown import ConversionOptions, convert


ICON_CLASSES = {
    "icon", "icons", "emoji", "fa", "fas", "far", "fal", "fab",
    "material-icons", "bi", "glyphicon", "lucide", "heroicon",
}

NON_CONTENT_TAGS = {
    "nav", "footer", "aside", "script", "style", "noscript",
    "iframe", "form", "button",
}

NON_CONTENT_ROLE_PATTERNS = (
    "navigation", "banner", "complementary", "search", "dialog", "alert",
)

NON_CONTENT_CLASS_ID_PATTERNS = (
    "nav", "navbar", "menu", "footer", "sidebar", "cookie", "modal",
    "popup", "banner", "breadcrumbs", "breadcrumb", "share", "social",
    "toolbar", "header-actions", "pagination", "comment", "comments",
    "related", "recommend", "ads", "advert", "promo", "newsletter",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert HTML to Markdown with optional cleanup."
    )
    parser.add_argument("source_html", help="Path to source HTML file")
    parser.add_argument("output_md", help="Path to output Markdown file")
    parser.add_argument(
        "--strip-svg",
        action="store_true",
        help="Remove all inline SVG elements before conversion",
    )
    parser.add_argument(
        "--strip-icons",
        action="store_true",
        help="Remove SVGs, icon tags, and decorative icon-like nodes",
    )
    parser.add_argument(
        "--main-content-only",
        action="store_true",
        help="Extract only the likely main content area",
    )
    return parser.parse_args()


def safe_attr(tag: Tag, name: str, default=None):
    if not isinstance(tag, Tag):
        return default
    attrs = getattr(tag, "attrs", None)
    if not isinstance(attrs, dict):
        return default
    return attrs.get(name, default)


def safe_classes(tag: Tag) -> list[str]:
    classes = safe_attr(tag, "class", [])
    if not classes:
        return []
    if isinstance(classes, str):
        return [classes]
    return [str(c) for c in classes]


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def has_icon_class(tag: Tag) -> bool:
    for cls in safe_classes(tag):
        if cls in ICON_CLASSES or cls.startswith("fa-") or cls.startswith("bi-"):
            return True
    return False


def strip_svg(soup: BeautifulSoup) -> None:
    for svg in list(soup.find_all("svg")):
        svg.decompose()


def strip_icons(soup: BeautifulSoup) -> None:
    strip_svg(soup)

    for tag in list(soup.find_all("i")):
        tag.decompose()

    for tag in list(soup.find_all(True)):
        if has_icon_class(tag):
            tag.decompose()
            continue

        aria_hidden = safe_attr(tag, "aria-hidden", "")
        if isinstance(aria_hidden, str) and aria_hidden.lower() == "true":
            tag.decompose()


def is_probably_non_content(tag: Tag) -> bool:
    if tag.name in NON_CONTENT_TAGS:
        return True

    role = safe_attr(tag, "role", "")
    if isinstance(role, str):
        role = role.lower()
        if any(pat in role for pat in NON_CONTENT_ROLE_PATTERNS):
            return True

    tag_id = safe_attr(tag, "id", "")
    if not isinstance(tag_id, str):
        tag_id = ""

    aria_label = safe_attr(tag, "aria-label", "")
    if not isinstance(aria_label, str):
        aria_label = ""

    attrs_text = " ".join([tag_id, " ".join(safe_classes(tag)), aria_label]).lower()
    return any(pat in attrs_text for pat in NON_CONTENT_CLASS_ID_PATTERNS)


def remove_non_content_elements(soup: BeautifulSoup) -> None:
    for tag in list(soup.find_all(True)):
        if is_probably_non_content(tag):
            tag.decompose()


def text_len(tag: Tag) -> int:
    return len(normalize_space(tag.get_text(" ", strip=True)))


def link_text_len(tag: Tag) -> int:
    total = 0
    for a in tag.find_all("a"):
        total += len(normalize_space(a.get_text(" ", strip=True)))
    return total


def score_candidate(tag: Tag) -> float:
    text = normalize_space(tag.get_text(" ", strip=True))
    if not text:
        return 0.0

    total_text = len(text)
    if total_text < 80:
        return 0.0

    p_count = len(tag.find_all("p"))
    li_count = len(tag.find_all("li"))
    heading_count = len(tag.find_all(re.compile(r"^h[1-6]$")))
    article_count = len(tag.find_all(["article", "section"]))
    link_ratio = link_text_len(tag) / max(total_text, 1)

    class_id = " ".join([str(safe_attr(tag, "id", "")), " ".join(safe_classes(tag))]).lower()

    bonus = 0.0
    if tag.name in {"main", "article"}:
        bonus += 120.0
    if "content" in class_id:
        bonus += 40.0
    if "article" in class_id or "post" in class_id:
        bonus += 50.0
    if "main" in class_id:
        bonus += 60.0

    penalty = 0.0
    if link_ratio > 0.6:
        penalty += 120.0
    elif link_ratio > 0.35:
        penalty += 50.0

    if is_probably_non_content(tag):
        penalty += 200.0

    return (
        total_text
        + p_count * 40
        + li_count * 6
        + heading_count * 18
        + article_count * 12
        + bonus
        - penalty
    )


def select_main_content_container(soup: BeautifulSoup) -> Tag | None:
    preferred = soup.select_one("main")
    if isinstance(preferred, Tag) and text_len(preferred) >= 80:
        return preferred

    preferred = soup.select_one("article")
    if isinstance(preferred, Tag) and text_len(preferred) >= 80:
        return preferred

    candidates: list[tuple[float, Tag]] = []
    for tag in soup.find_all(["main", "article", "section", "div"]):
        score = score_candidate(tag)
        if score > 0:
            candidates.append((score, tag))

    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    body = soup.body
    if isinstance(body, Tag):
        return body
    return None


def extract_main_content_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    remove_non_content_elements(soup)

    container = select_main_content_container(soup)
    if container is None:
        return html

    return str(container)


def preprocess_html(html: str, args: argparse.Namespace) -> str:
    soup = BeautifulSoup(html, "html.parser")

    if args.strip_icons:
        strip_icons(soup)
    elif args.strip_svg:
        strip_svg(soup)

    processed_html = str(soup)

    if args.main_content_only:
        processed_html = extract_main_content_html(processed_html)

    return processed_html


def main() -> int:
    args = parse_args()

    source_path = Path(args.source_html)
    output_path = Path(args.output_md)

    if not source_path.exists():
        print(f"Error: source file does not exist: {source_path}", file=sys.stderr)
        return 1

    if not source_path.is_file():
        print(f"Error: source path is not a file: {source_path}", file=sys.stderr)
        return 1

    try:
        html = source_path.read_text(encoding="utf-8")
    except Exception as exc:
        print(f"Error reading source file: {exc}", file=sys.stderr)
        return 1

    try:
        html = preprocess_html(html, args)
    except Exception as exc:
        print(f"Error preprocessing HTML: {exc}", file=sys.stderr)
        return 1

    options = ConversionOptions(
        heading_style="atx",
        list_indent_width=2,
    )

    try:
        markdown = convert(html, options)
    except Exception as exc:
        print(f"Error converting HTML to Markdown: {exc}", file=sys.stderr)
        return 1

    markdown = markdown.strip() + "\n"

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
    except Exception as exc:
        print(f"Error writing output file: {exc}", file=sys.stderr)
        return 1

    print(f"Markdown written to: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())