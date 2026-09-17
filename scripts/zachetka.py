"""Зачётка Сессии 0: HTML из Session0/Зачётка.html → PDF."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = REPO_ROOT / "Session0" / "Зачётка.html"
OUT_DIR = REPO_ROOT / "ForPrint" / "ReadyForPrint"
SESSION_DIR = REPO_ROOT / "ForPrint" / "Сессия0"
OUT_NAME = "Зачётка-Сессия0"
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
EDGE_ALT = Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe")

DEFAULT_GROUP = "П-0 / IV"
PLAYERS = [
    ("Артас", "0-0417"),
    ("Эона", "0-0418"),
    ("Готрек", "0-0419"),
]

BOOKLET_RE = re.compile(
    r"<!-- booklet:.*?-->\s*(.*?)\s*<!-- /booklet -->",
    re.DOTALL,
)


def fill(block: str, number: str, group: str) -> str:
    return block.replace("{{NUMBER}}", number).replace("{{GROUP}}", group)


def build_html(
    template: str,
    numbers: list[str],
    group: str,
    rotate_inner: bool,
    title: str | None = None,
) -> str:
    match = BOOKLET_RE.search(template)
    if not match:
        raise SystemExit("В HTML нет блока <!-- booklet --> … <!-- /booklet -->")
    src = match.group(1)
    copies = []
    for n in numbers:
        html = fill(src, n, group)
        if rotate_inner:
            html = html.replace('class="sheet inner"', 'class="sheet inner rot"', 1)
        copies.append(html)
    body = "\n".join(copies)
    out = BOOKLET_RE.sub(body, template, count=1)
    if title:
        out = re.sub(
            r"<title>.*?</title>",
            f"<title>{title}</title>",
            out,
            count=1,
        )
    return out


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
    parser = argparse.ArgumentParser(description="Зачётка Сессии 0 → PDF")
    parser.add_argument("--group", default=DEFAULT_GROUP, help="номер группы")
    parser.add_argument(
        "--flip",
        choices=("short", "long"),
        default="short",
        help="переворот при двусторонней печати (по умолчанию short)",
    )
    parser.add_argument(
        "--combined",
        action="store_true",
        help="один PDF со всеми книжками в ReadyForPrint",
    )
    args = parser.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    if not TEMPLATE.is_file():
        raise SystemExit(f"Нет шаблона: {TEMPLATE.relative_to(REPO_ROOT)}")
    template = TEMPLATE.read_text(encoding="utf-8")
    rotate = args.flip == "long"
    SESSION_DIR.mkdir(parents=True, exist_ok=True)

    for name, number in PLAYERS:
        title = f"Зачётный лист — {name} — {number}"
        html_text = build_html(template, [number], args.group, rotate, title)
        html_path = SESSION_DIR / f"Зачётка-{name}.html"
        pdf_path = SESSION_DIR / f"Зачётка-{name}.pdf"
        html_path.write_text(html_text, encoding="utf-8")
        print_pdf(html_text, pdf_path)
        print(html_path.relative_to(REPO_ROOT).as_posix())
        print(pdf_path.relative_to(REPO_ROOT).as_posix())

    if args.combined:
        numbers = [number for _, number in PLAYERS]
        html_text = build_html(template, numbers, args.group, rotate)
        suffix = "" if args.flip == "short" else "-long"
        out = OUT_DIR / f"{OUT_NAME}{suffix}.pdf"
        print_pdf(html_text, out)
        print(out.relative_to(REPO_ROOT).as_posix())


if __name__ == "__main__":
    sys.exit(main())
