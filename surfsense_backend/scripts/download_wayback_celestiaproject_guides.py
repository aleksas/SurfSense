#!/usr/bin/env python3
"""
Download CelestiaProject guides via Wayback and optionally ingest into SurfSense.

Use case:
- `https://celestiaproject.space/guides.html` is protected by anti-bot in live mode.
- Wayback snapshots are accessible and include scripting/user-guide links.
- This script pulls english scripting/user-guide docs and can ingest them.

Examples (inside backend container):
  python /app/scripts/download_wayback_celestiaproject_guides.py --download-only
  python /app/scripts/download_wayback_celestiaproject_guides.py --email test@example.com --ingest
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
import zipfile
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests


WAYBACK_CDX = "https://web.archive.org/cdx/search/cdx"
GUIDES_URL = "https://celestiaproject.space/guides.html"


@dataclass(frozen=True)
class Link:
    text: str
    url: str


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._href: str | None = None
        self._txt: list[str] = []
        self.links: list[Link] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() != "a":
            return
        d = dict(attrs)
        href = d.get("href")
        if not href:
            return
        self._href = href
        self._txt = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._txt.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a":
            return
        if not self._href:
            return
        text = "".join(self._txt).strip()
        self.links.append(Link(text=text, url=self._href))
        self._href = None
        self._txt = []


def _sanitize_name(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"[^A-Za-z0-9._ -]+", "", s)
    s = s.replace(" ", "_")
    return s[:160] or "doc"


def _is_english(text: str, url: str) -> bool:
    if re.search(
        r"\b(French|German|Italian|Spanish|Russian|Polish|Portuguese|Japanese|Chinese|Korean)\b",
        text,
        flags=re.I,
    ):
        return False
    if re.search(
        r"(\bRUS\b|_RU\b|\bCN\b|\bDE\b|\bFR\b|\bIT\b|\bES\b|\bJP\b|\bKR\b)",
        url,
        flags=re.I,
    ):
        return False
    if re.search(r"[А-Яа-я]", text):
        return False
    # Additional non-English markers seen in this catalog.
    if re.search(r"\b(Datei|Dokument|Handbuch|Documento|Guida|Leer|Lire)\b", text, flags=re.I):
        return False
    return True


def _is_scripting_related(text: str, url: str) -> bool:
    t = f"{text} {url}".lower()
    keys = [
        "scripting",
        "script",
        "celx",
        "lua",
        "ssc",
        "stc",
        "dsc",
        "spice",
        "kml",
        "user guide",
        "users guide",
        "user's guide",
        "cel-guide-en",
        "cel-script-guide-en",
        "celscriptingguide",
    ]
    return any(k in t for k in keys)


def _wanted_extension(url: str) -> bool:
    path = urlparse(url).path.lower()
    if path.endswith("/cc/cel-script-guide-en") or path.endswith("/cc/cel-guide-en"):
        return True
    return any(
        path.endswith(ext)
        for ext in (
            ".htm",
            ".html",
            ".txt",
            ".rtf",
            ".pdf",
            ".doc",
            ".docx",
            ".zip",
        )
    )


def _cdx_latest_timestamp(session: requests.Session, url: str) -> str | None:
    params = {
        "url": url,
        "output": "json",
        "fl": "timestamp,original,statuscode,mimetype",
        "filter": "statuscode:200",
        "collapse": "digest",
        "limit": "1",
        "sort": "reverse",
    }
    try:
        r = session.get(WAYBACK_CDX, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return None
    if not isinstance(data, list) or len(data) < 2:
        return None
    row = data[1]
    if not isinstance(row, list) or not row:
        return None
    return str(row[0])


def _wayback_raw_url(timestamp: str, original_url: str) -> str:
    return f"https://web.archive.org/web/{timestamp}id_/{original_url}"


def _fetch_text_with_retries(session: requests.Session, url: str, retries: int = 3) -> str:
    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            r = session.get(url, timeout=45)
            r.raise_for_status()
            return r.text
        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(1.2 * attempt)
                continue
    raise RuntimeError(f"Failed to fetch text: {url}: {last_err}")


def _download_stream(session: requests.Session, url: str, dest: Path, retries: int = 3) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
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
            if attempt < retries:
                time.sleep(1.4 * attempt)
                continue
    raise RuntimeError(f"Failed download: {url}: {last_err}")


def _maybe_unzip(path: Path, out_dir: Path) -> None:
    if path.suffix.lower() != ".zip":
        return
    try:
        with zipfile.ZipFile(path, "r") as zf:
            zf.extractall(out_dir)
    except Exception as e:
        print(f"WARN: unzip failed for {path.name}: {e}", file=sys.stderr)


def _resolve_to_wayback_if_possible(session: requests.Session, url: str) -> str:
    ts = _cdx_latest_timestamp(session, url)
    if ts:
        return _wayback_raw_url(ts, url)
    return url


def _select_links_from_guides(html: str) -> list[Link]:
    parser = _LinkParser()
    parser.feed(html)
    out: list[Link] = []
    for link in parser.links:
        href = link.url.strip()
        if not href or href.startswith("#"):
            continue
        full = urljoin(GUIDES_URL, href)
        out.append(Link(text=link.text, url=full))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--email", default=None, help="SurfSense user email (required for --ingest).")
    ap.add_argument("--search-space-id", type=int, default=None)
    ap.add_argument("--out-folder", default="/tmp/celestia_wayback_guides_docs")
    ap.add_argument("--limit", type=int, default=30)
    ap.add_argument("--download-only", action="store_true")
    ap.add_argument("--ingest", action="store_true", help="Run ingest_docs_tree.py after download.")
    args = ap.parse_args()

    if args.ingest and not args.email:
        print("ERROR: --email is required with --ingest", file=sys.stderr)
        return 2

    out_root = Path(args.out_folder)
    out_root.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Wayback SurfSense indexer)"})

    guides_ts = _cdx_latest_timestamp(session, GUIDES_URL)
    if not guides_ts:
        print("ERROR: no Wayback snapshot found for guides.html", file=sys.stderr)
        return 2
    guides_wayback_url = _wayback_raw_url(guides_ts, GUIDES_URL)
    print(f"guides_snapshot={guides_ts} {guides_wayback_url}")

    guides_html = _fetch_text_with_retries(session, guides_wayback_url)
    links = _select_links_from_guides(guides_html)
    print(f"guides_links={len(links)}")

    selected: list[Link] = []
    for link in links:
        if not link.text:
            continue
        if not _is_english(link.text, link.url):
            continue
        if not _is_scripting_related(link.text, link.url):
            continue
        if not _wanted_extension(link.url):
            continue
        if re.search(r"(contactus|contactform|mailto:|twitter|github)", link.url, flags=re.I):
            continue
        selected.append(link)

    # Add explicit target from share.google-resolved page as a hard requirement.
    selected.append(
        Link(
            text="Celestia .CEL Scripting Guide (ver. 1.0g) [explicit]",
            url="https://celestiaproject.space/docs/CELScriptingGuide/Cel_Script_Guide_v1_0g.htm",
        )
    )
    selected.append(
        Link(
            text="Celestia .CEL Scripting Guide (RTF) [explicit]",
            url="http://www.celestiamotherlode.net/creators/dgoyette/Cel_Script_Guide_v1-0g.rtf",
        )
    )

    # De-dup by normalized URL.
    dedup: list[Link] = []
    seen: set[str] = set()
    for link in selected:
        u = link.url
        if u in seen:
            continue
        seen.add(u)
        dedup.append(link)

    if args.limit is not None:
        dedup = dedup[: max(0, args.limit)]
    print(f"selected={len(dedup)}")

    for i, link in enumerate(dedup, start=1):
        original = link.url
        parsed = urlparse(original)
        host = parsed.netloc.lower()

        download_url = original
        # Prefer archived raw for celestiaproject-space links (anti-bot bypass).
        if "celestiaproject.space" in host:
            download_url = _resolve_to_wayback_if_possible(session, original)

        base_name = Path(parsed.path).name or _sanitize_name(link.text)
        if "." not in base_name:
            # Extensionless pages (e.g. /cc/cel-script-guide-en) are HTML.
            base_name = f"{base_name}.html"
        file_name = f"{i:03d}__{_sanitize_name(link.text)}__{base_name}"
        dest = out_root / file_name

        try:
            print(f"[{i}/{len(dedup)}] {original} -> {download_url} -> {dest}")
            _download_stream(session, download_url, dest)
            _maybe_unzip(dest, out_root / (dest.stem + "_unzipped"))
        except Exception as e:
            print(f"WARN: failed {original}: {e}", file=sys.stderr)

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
