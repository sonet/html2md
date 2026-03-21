#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path

from bs4 import BeautifulSoup
from html_to_markdown import ConversionOptions, convert


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert HTML to Markdown with optional cleanup."
    )
    parser.add_argument("source_html", help="Path to source HTML file")
    parser.add_argument("output_md", help="Path to output Markdown file")

    parser.add_argument(
        "--strip-svg",
        action="store_true",
        help="Remove all <svg> elements",
    )

    parser.add_argument(
        "--strip-icons",
        action="store_true",
        help="Remove common icon elements (svg, icon classes, aria-hidden)",
    )

    return parser.parse_args()


def strip_svg(soup: BeautifulSoup):
    for svg in soup.find_all("svg"):
        svg.decompose()


def strip_icons(soup: BeautifulSoup):
    # 1. Remove all SVGs (icons/emojis)
    strip_svg(soup)

    # 2. Remove <i> tags (FontAwesome, etc.)
    for tag in soup.find_all("i"):
        tag.decompose()

    # 3. Remove elements with common icon classes
    ICON_CLASSES = [
        "icon", "emoji", "fa", "fas", "far", "fal", "fab",
        "material-icons", "bi"
    ]

    for tag in soup.find_all(True):
        classes = tag.get("class", [])
        if any(cls in ICON_CLASSES or cls.startswith("fa-") for cls in classes):
            tag.decompose()
            continue

        # 4. Remove aria-hidden (decorative icons)
        if tag.get("aria-hidden") == "true":
            tag.decompose()


def preprocess_html(html: str, args) -> str:
    soup = BeautifulSoup(html, "html.parser")

    if args.strip_icons:
        strip_icons(soup)
    elif args.strip_svg:
        strip_svg(soup)

    return str(soup)


def main() -> int:
    args = parse_args()

    source_path = Path(args.source_html)
    output_path = Path(args.output_md)

    if not source_path.exists():
        print(f"Error: source file does not exist: {source_path}", file=sys.stderr)
        return 1

    try:
        html = source_path.read_text(encoding="utf-8")
    except Exception as exc:
        print(f"Error reading file: {exc}", file=sys.stderr)
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
        print(f"Error converting HTML: {exc}", file=sys.stderr)
        return 1

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
    except Exception as exc:
        print(f"Error writing file: {exc}", file=sys.stderr)
        return 1

    print(f"✅ Markdown written to: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())