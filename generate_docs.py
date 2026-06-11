#!/usr/bin/env python3
"""
Generate PDF documentation from Markdown files.

Usage:
  python generate_docs.py README.md output.pdf
  python generate_docs.py CASE_STUDY.md case_study.pdf

Requires: pip install weasyprint markdown
"""
import sys
import markdown
import weasyprint

CSS = """
body {
    font-family: 'DejaVu Sans Mono', monospace;
    font-size: 10pt;
    margin: 2cm;
    color: #1e293b;
    line-height: 1.6;
}
h1 {
    font-size: 18pt;
    color: #1a1a2e;
    border-bottom: 2px solid #16213e;
    padding-bottom: 6px;
}
h2 {
    font-size: 14pt;
    color: #16213e;
    margin-top: 24px;
}
h3 {
    font-size: 12pt;
    color: #1e293b;
}
pre {
    background: #f8fafc;
    padding: 10px;
    border-radius: 4px;
    font-size: 8pt;
    border: 1px solid #e2e8f0;
    overflow-x: auto;
}
code {
    background: #f1f5f9;
    padding: 1px 5px;
    border-radius: 3px;
    font-size: 9pt;
}
img {
    max-width: 100%;
    height: auto;
}
table {
    border-collapse: collapse;
    width: 100%;
    margin: 12px 0;
}
th, td {
    border: 1px solid #cbd5e1;
    padding: 6px 10px;
    text-align: left;
    font-size: 9pt;
}
th {
    background: #f1f5f9;
    font-weight: 600;
}
blockquote {
    border-left: 4px solid #2563eb;
    padding-left: 16px;
    margin: 16px 0;
    color: #475569;
    font-style: italic;
}
p {
    margin: 8px 0;
}
"""


def convert(md_path: str, pdf_path: str) -> None:
    md_content = open(md_path).read()
    html_body = markdown.markdown(
        md_content,
        extensions=['fenced_code', 'tables', 'codehilite', 'nl2br'],
    )
    html_doc = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>{CSS}</style>
</head><body>{html_body}</body></html>"""
    weasyprint.HTML(string=html_doc).write_pdf(pdf_path)
    print(f"Generated: {pdf_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python generate_docs.py input.md output.pdf")
        sys.exit(1)
    convert(sys.argv[1], sys.argv[2])
