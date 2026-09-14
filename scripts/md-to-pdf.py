"""Markdown from ForPrint -> PDF in ForPrint/ReadyForPrint."""

from __future__ import annotations

import argparse
import html
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FOR_PRINT = REPO_ROOT / "ForPrint"
OUT_DIR = FOR_PRINT / "ReadyForPrint"
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
EDGE_ALT = Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe")

CSS = """
@page { size: A4; margin: 14mm 16mm; }
html, body { margin: 0; padding: 0; }
body {
  font-family: "Times New Roman", "Segoe UI", serif;
  font-size: 13pt;
  line-height: 1.35;
  color: #111;
}
h1 { font-size: 18pt; margin: 0 0 0.6em; }
h2 { font-size: 14pt; margin: 1em 0 0.4em; }
h3 { font-size: 13pt; margin: 0.8em 0 0.3em; }
p { margin: 0 0 0.55em; }
ul, ol { margin: 0 0 0.7em; padding-left: 1.3em; }
li { margin: 0 0 0.2em; }
strong { font-weight: 700; }
code { font-family: Consolas, "Courier New", monospace; font-size: 0.92em; }
"""


def inline_md(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", text)
    return text


def md_to_html(md: str) -> str:
    lines = md.replace("\r\n", "\n").split("\n")
    body: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith("### "):
            body.append(f"<h3>{inline_md(line[4:].strip())}</h3>")
            i += 1
            continue
        if line.startswith("## "):
            body.append(f"<h2>{inline_md(line[3:].strip())}</h2>")
            i += 1
            continue
        if line.startswith("# "):
            body.append(f"<h1>{inline_md(line[2:].strip())}</h1>")
            i += 1
            continue
        if re.match(r"^[-*] ", line):
            items: list[str] = []
            while i < len(lines) and re.match(r"^[-*] ", lines[i]):
                items.append(f"<li>{inline_md(lines[i][2:].strip())}</li>")
                i += 1
            body.append("<ul>" + "".join(items) + "</ul>")
            continue
        if re.match(r"^\d+\. ", line):
            items = []
            while i < len(lines) and re.match(r"^\d+\. ", lines[i]):
                items.append(
                    f"<li>{inline_md(re.sub(r'^\d+\. ', '', lines[i]).strip())}</li>"
                )
                i += 1
            body.append("<ol>" + "".join(items) + "</ol>")
            continue
        para = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not _starts_block(lines[i]):
            para.append(lines[i])
            i += 1
        body.append(f"<p>{inline_md(' '.join(p.strip() for p in para))}</p>")
    return (
        "<!DOCTYPE html><html lang='ru'><head><meta charset='utf-8'>"
        f"<style>{CSS}</style></head><body>{''.join(body)}</body></html>"
    )


def _starts_block(line: str) -> bool:
    return bool(
        line.startswith("#")
        or re.match(r"^[-*] ", line)
        or re.match(r"^\d+\. ", line)
    )


def resolve_source(arg: str) -> Path:
    raw = Path(arg)
    candidates = []
    if raw.is_file():
        return raw.resolve()
    candidates.append(REPO_ROOT / arg)
    candidates.append(FOR_PRINT / arg)
    for c in candidates:
        if c.is_file():
            return c.resolve()
    key = arg.strip()
    if re.fullmatch(r"\d{1,4}", key):
        key = key.zfill(4)
        matches = list(FOR_PRINT.rglob(f"{key}-*.md"))
        if len(matches) == 1:
            return matches[0].resolve()
        if len(matches) > 1:
            listed = "\n".join(str(m.relative_to(REPO_ROOT)) for m in matches)
            raise SystemExit(f"Несколько файлов с ключом {key}:\n{listed}")
    raise SystemExit(f"Не найден md: {arg}")


def find_edge() -> Path:
    for p in (EDGE, EDGE_ALT):
        if p.is_file():
            return p
    raise SystemExit("Не найден Microsoft Edge.")


def print_pdf(html_text: str, pdf_path: Path) -> None:
    edge = find_edge()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        html_file = tmp_dir / "doc.html"
        tmp_pdf = tmp_dir / "doc.pdf"
        html_file.write_text(html_text, encoding="utf-8")
        cmd = [
            str(edge),
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={tmp_pdf}",
            html_file.resolve().as_uri(),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0 or not tmp_pdf.is_file():
            raise SystemExit(
                "Edge не собрал PDF.\n"
                + (proc.stderr or proc.stdout or f"код {proc.returncode}")
            )
        pdf_path.write_bytes(tmp_pdf.read_bytes())


def main() -> None:
    parser = argparse.ArgumentParser(description="MD из ForPrint → PDF в ReadyForPrint")
    parser.add_argument("source", help="путь к md, относительный путь или ключ 0001")
    args = parser.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    source = resolve_source(args.source)
    if FOR_PRINT not in source.parents and source.parent != FOR_PRINT:
        raise SystemExit("Файл должен быть внутри ForPrint/")
    html_text = md_to_html(source.read_text(encoding="utf-8"))
    out = OUT_DIR / f"{source.stem}.pdf"
    print_pdf(html_text, out)
    print(out.relative_to(REPO_ROOT).as_posix())


if __name__ == "__main__":
    sys.exit(main())
