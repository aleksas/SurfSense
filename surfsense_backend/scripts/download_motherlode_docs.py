#!/usr/bin/env python3
"""
Download Celestia Motherlode documentation (scripting + user guides) and optionally ingest into SurfSense.

Why:
- Some Celestia guides are hosted on sites protected by anti-bot (Anubis).
- Motherlode has a stable list and direct downloads over HTTP.
- SurfSense can then be used to ask for grounded script improvements or generate flybys.

Run (inside backend container):
  python /app/scripts/download_motherlode_docs.py --out-folder /tmp/celestia_motherlode_docs

Download + ingest into the user's search space:
  python /app/scripts/download_motherlode_docs.py --email test@example.com --ingest
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests


CATALOG_URLS = [
    "http://www.celestiamotherlode.net/catalog/documentation.html",
    "http://celestiamotherlode.net/catalog/documentation.html",
]


@dataclass(frozen=True)
class Link:
    text: str
    url: str


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._href: str | None = None
        self._text_parts: list[str] = []
        self.links: list[Link] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() != "a":
            return
        d = dict(attrs)
        href = d.get("href")
        if not href:
            return
        self._href = href
        self._text_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a":
            return
        if not self._href:
            return
        text = "".join(self._text_parts).strip()
        self.links.append(Link(text=text, url=self._href))
        self._href = None
        self._text_parts = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text_parts.append(data)


def _sanitize_name(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"[^A-Za-z0-9._ -]+", "", s)
    s = s.replace(" ", "_")
    return s[:160] or "doc"


def _is_english(text: str) -> bool:
    # Motherlode uses tags like "(French)" in link text for translations.
    if re.search(
        r"\b(French|German|Italian|Spanish|Russian|Polish|Portuguese|Japanese|Chinese|Korean)\b",
        text,
        flags=re.I,
    ):
        return False
    return True


def _looks_non_english_url(url: str) -> bool:
    # Common language markers in filenames.
    return bool(
        re.search(
            r"(\bRUS\b|\bFRA\b|\bFR\b|\bDEU\b|\bDE\b|\bITA\b|\bIT\b|\bESP\b|\bES\b|\bPOL\b|\bPT\b|\bJPN\b|\bJP\b|\bCHN\b|\bCN\b|\bKOR\b|\bKR\b)",
            url,
            flags=re.I,
        )
    )


def _is_scripting_related(text: str, url: str) -> bool:
    t = f"{text} {url}".lower()
    keywords = [
        "scripting",
        "script",
        "celx",
        "lua",
        "ssc",
        "stc",
        "dsc",
        "spice",
        "kml",
        "user's guide",
        "users guide",
        "user guide",
    ]
    return any(k in t for k in keywords)


def _wanted_extension(url: str) -> bool:
    path = urlparse(url).path.lower()
    return any(
        path.endswith(ext)
        for ext in (
            ".zip",
            ".pdf",
            ".doc",
            ".docx",
            ".rtf",
            ".txt",
            ".html",
            ".htm",
        )
    )


def _fetch_links(session: requests.Session, catalog_urls: list[str]) -> list[Link]:
    last_err: Exception | None = None
    for url in catalog_urls:
        try:
            r = session.get(url, timeout=30, allow_redirects=True)
            r.raise_for_status()
            base_url = r.url
            html = r.text
            break
        except Exception as e:
            last_err = e
    else:
        raise RuntimeError(f"Failed to fetch Motherlode catalog from {catalog_urls}: {last_err}")

    p = _LinkParser()
    p.feed(html)

    out: list[Link] = []
    for link in p.links:
        if not link.url or link.url.startswith("#"):
            continue
        full = urljoin(base_url, link.url)
        out.append(Link(text=link.text, url=full))
    return out


def _download(session: requests.Session, url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    last_err: Exception | None = None
    for attempt in range(1, 4):
        try:
            with session.get(url, timeout=60, stream=True) as r:
                r.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 256):
                        if chunk:
                            f.write(chunk)
            return
        except Exception as e:
            last_err = e
            # Basic retry/backoff; keep dependencies minimal.
            if attempt < 3:
                import time

                time.sleep(1.5 * attempt)
                continue
            raise last_err


def _maybe_unzip(path: Path, out_dir: Path) -> None:
    if path.suffix.lower() != ".zip":
        return
    try:
        with zipfile.ZipFile(path, "r") as zf:
            zf.extractall(out_dir)
    except Exception as e:
        print(f"WARN: failed to unzip {path.name}: {e}", file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--email", default=None, help="SurfSense user email (required for --ingest).")
    ap.add_argument("--search-space-id", type=int, default=None)
    ap.add_argument("--out-folder", default="/tmp/celestia_motherlode_docs")
    ap.add_argument("--limit", type=int, default=30)
    ap.add_argument("--download-only", action="store_true")
    ap.add_argument(
        "--allow-external",
        action="store_true",
        help="Allow downloads from non-motherlode hosts (default: only celestiamotherlode.net).",
    )
    ap.add_argument("--ingest", action="store_true", help="Run ingest_docs_tree.py after download.")
    args = ap.parse_args()

    if args.ingest and not args.email:
        print("ERROR: --email is required when using --ingest", file=sys.stderr)
        return 2

    out_root = Path(args.out_folder)
    out_root.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (SurfSense Celestia indexer)"})

    links = _fetch_links(session, CATALOG_URLS)

    selected: list[Link] = []
    for link in links:
        if not link.text:
            continue
        if not _is_english(link.text):
            continue
        if _looks_non_english_url(link.url):
            continue
        if not args.allow_external:
            host = urlparse(link.url).netloc.lower()
            if not host.endswith("celestiamotherlode.net"):
                continue
        # Guardrails: the Motherlode catalog includes non-doc links; avoid obvious non-doc areas.
        if re.search(r"(contactus|contactform|/php/)", link.url, flags=re.I):
            continue
        if not _is_scripting_related(link.text, link.url):
            continue
        if not _wanted_extension(link.url):
            continue
        selected.append(link)

    # De-dup by URL while keeping order.
    seen: set[str] = set()
    deduped: list[Link] = []
    for l in selected:
        if l.url in seen:
            continue
        seen.add(l.url)
        deduped.append(l)

    if args.limit is not None:
        deduped = deduped[: max(0, args.limit)]

    print(f"Motherlode links: {len(links)}")
    print(f"Selected (english + scripting/user-guide): {len(deduped)}")

    for i, link in enumerate(deduped, start=1):
        url_path = urlparse(link.url).path
        base = Path(url_path).name
        if not base:
            base = _sanitize_name(link.text) + ".bin"
        name = f"{i:03d}__{_sanitize_name(link.text)}__{base}"

        dest = out_root / name
        try:
            print(f"[{i}/{len(deduped)}] download {link.url} -> {dest}")
            _download(session, link.url, dest)
            _maybe_unzip(dest, out_root / (dest.stem + "_unzipped"))
        except Exception as e:
            print(f"WARN: download failed for {link.url}: {e}", file=sys.stderr)

    if args.download_only and args.ingest:
        print("WARN: both --download-only and --ingest set; proceeding with ingest.", file=sys.stderr)

    if args.ingest and not args.download_only:
        cmd = [
            sys.executable,
            "/app/scripts/ingest_docs_tree.py",
            "--email",
            args.email,
            "--folder",
            str(out_root),
            "--glob",
            "**/*",
            "--extensions",
            ".md,.txt,.rst,.adoc,.html,.htm,.rtf,.pdf,.doc,.docx",
            "--reindex-existing",
        ]
        if args.search_space_id is not None:
            cmd.extend(["--search-space-id", str(args.search_space_id)])

        print("Ingest:", " ".join(cmd))
        env = os.environ.copy()
        # Avoid any interactive surprises.
        env.setdefault("PYTHONUNBUFFERED", "1")
        return subprocess.run(cmd, env=env, check=False).returncode

    print(f"Done. Downloaded into: {out_root}")
    if not args.ingest:
        print(
            "Next: python /app/scripts/ingest_docs_tree.py "
            f"--email <your_email> --folder {out_root} --glob '**/*' --reindex-existing"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
