#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path

from html_to_markdown import ConversionOptions, convert


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert an HTML file to a Markdown file."
    )
    parser.add_argument(
        "source_html",
        help="Path to the source HTML file",
    )
    parser.add_argument(
        "output_md",
        help="Path to the output Markdown file",
    )
    return parser.parse_args()


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

    options = ConversionOptions(
        heading_style="atx",
        list_indent_width=2,
    )

    try:
        markdown = convert(html, options)
    except Exception as exc:
        print(f"Error converting HTML to Markdown: {exc}", file=sys.stderr)
        return 1

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