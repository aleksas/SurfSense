#!/usr/bin/env python3
import argparse
import asyncio
import json
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.db import async_session_maker
from app.services.connector_service import ConnectorService


@dataclass
class TestCase:
    case_id: str
    query: str
    expected_thread_file: str
    expected_post_num: str
    expected_post_id: str
    expected_author: str
    anchor_text: str
    narrowing_tokens: list[str]


def _strip_wrapping_quotes(text: str) -> str:
    text = text.strip()
    if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
        return text[1:-1]
    return text


def parse_cases(markdown_path: Path) -> list[TestCase]:
    lines = markdown_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    cases: list[TestCase] = []
    cur: dict[str, Any] = {}

    post_re = re.compile(
        r"^- Expected post: `Post #(?P<num>[^`]+)` \(ID `(?P<id>[^`]+)`\), author `(?P<author>[^`]+)`$"
    )

    def flush() -> None:
        nonlocal cur
        if not cur:
            return
        required = {
            "case_id",
            "query",
            "expected_thread_file",
            "expected_post_num",
            "expected_post_id",
            "expected_author",
            "anchor_text",
            "narrowing_tokens",
        }
        missing = required - set(cur.keys())
        if missing:
            raise ValueError(f"Incomplete case {cur.get('case_id', '<unknown>')}: missing {sorted(missing)}")
        cases.append(
            TestCase(
                case_id=cur["case_id"],
                query=cur["query"],
                expected_thread_file=cur["expected_thread_file"],
                expected_post_num=cur["expected_post_num"],
                expected_post_id=cur["expected_post_id"],
                expected_author=cur["expected_author"],
                anchor_text=cur["anchor_text"],
                narrowing_tokens=cur["narrowing_tokens"],
            )
        )
        cur = {}

    for line in lines:
        if line.startswith("## TC-"):
            flush()
            cur["case_id"] = line.replace("## ", "", 1).strip()
            continue

        if not cur:
            continue

        if line.startswith("- Query: "):
            cur["query"] = line.replace("- Query: ", "", 1).strip()
            continue

        if line.startswith("- Expected thread file: "):
            m = re.match(r"^- Expected thread file: `(.+)`$", line)
            if not m:
                raise ValueError(f"Failed parsing expected thread line for {cur.get('case_id')}: {line}")
            cur["expected_thread_file"] = m.group(1).strip()
            continue

        if line.startswith("- Expected post: "):
            m = post_re.match(line)
            if not m:
                raise ValueError(f"Failed parsing expected post line for {cur.get('case_id')}: {line}")
            cur["expected_post_num"] = m.group("num").strip()
            cur["expected_post_id"] = m.group("id").strip()
            cur["expected_author"] = m.group("author").strip()
            continue

        if line.startswith("- Anchor text: "):
            raw = line.replace("- Anchor text: ", "", 1).strip()
            cur["anchor_text"] = _strip_wrapping_quotes(raw)
            continue

        if line.startswith("- Narrowing tokens: "):
            raw = line.replace("- Narrowing tokens: ", "", 1).strip()
            cur["narrowing_tokens"] = [tok.strip().strip("`") for tok in raw.split(",") if tok.strip()]
            continue

    flush()
    return cases


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-z0-9]+", "", text)
    return text


def hit_text(hit: dict[str, Any]) -> str:
    parts: list[str] = []
    content = hit.get("content")
    if isinstance(content, str):
        parts.append(content)
    for chunk in hit.get("chunks") or []:
        c = chunk.get("content")
        if isinstance(c, str):
            parts.append(c)
    return "\n".join(parts)


def title_for_hit(hit: dict[str, Any]) -> str:
    doc = hit.get("document") or {}
    return str(doc.get("title") or "")


def strict_match(case: TestCase, hit: dict[str, Any]) -> tuple[bool, dict[str, bool]]:
    title = title_for_hit(hit)
    text = hit_text(hit)
    ntext = normalize_text(text)
    nanchor = normalize_text(case.anchor_text)

    # We switched forum ingestion from thread-level documents (thread_1234.md)
    # to post-level documents (thread_1234__post_p56789.md). Treat a post-level
    # doc as a thread match if it shares the thread prefix.
    expected_thread_prefix = case.expected_thread_file.removesuffix(".md") + "__"
    thread_match = title == case.expected_thread_file or title.startswith(expected_thread_prefix)

    checks = {
        "thread_match": thread_match,
        # Post ID is always present in post-level document titles even if the
        # chunker returns only the body (without the header lines).
        "post_id_match": (case.expected_post_id in title) or (case.expected_post_id in text),
        "anchor_match": nanchor in ntext if nanchor else False,
    }
    return all(checks.values()), checks


def filter_hits(docs: list[dict[str, Any]], exclude_titles: set[str]) -> list[dict[str, Any]]:
    if not exclude_titles:
        return docs
    return [d for d in docs if title_for_hit(d) not in exclude_titles]


async def run_cases(
    cases: list[TestCase],
    search_space_id: int,
    top_k: int,
    progress_every: int,
    exclude_titles: set[str] | None = None,
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    summary = {
        "total_cases": len(cases),
        "top1_strict_passes": 0,
        "top3_strict_passes": 0,
        "top1_thread_match": 0,
        "top1_post_id_match": 0,
        "top1_anchor_match": 0,
        "errors": 0,
    }

    started = time.perf_counter()
    exclude_titles = exclude_titles or set()
    async with async_session_maker() as session:
        svc = ConnectorService(session, search_space_id=search_space_id)
        for i, case in enumerate(cases, 1):
            case_start = time.perf_counter()
            row: dict[str, Any] = {
                "case_id": case.case_id,
                "query": case.query,
                "expected_thread_file": case.expected_thread_file,
                "expected_post_id": case.expected_post_id,
                "expected_post_num": case.expected_post_num,
            }
            try:
                _sources, docs = await svc.search_files(
                    user_query=case.query,
                    search_space_id=search_space_id,
                    top_k=top_k,
                )
                docs = filter_hits(docs, exclude_titles)
                row["retrieved_count"] = len(docs)
                top1_hit = docs[0] if docs else None
                if top1_hit is None:
                    row["top1_strict_pass"] = False
                    row["top3_strict_pass"] = False
                    row["top1_checks"] = {
                        "thread_match": False,
                        "post_id_match": False,
                        "anchor_match": False,
                    }
                    row["top1_title"] = None
                else:
                    top1_pass, top1_checks = strict_match(case, top1_hit)
                    row["top1_strict_pass"] = top1_pass
                    row["top1_checks"] = top1_checks
                    row["top1_title"] = title_for_hit(top1_hit)
                    row["top1_preview"] = hit_text(top1_hit)[:260]

                    summary["top1_thread_match"] += int(top1_checks["thread_match"])
                    summary["top1_post_id_match"] += int(top1_checks["post_id_match"])
                    summary["top1_anchor_match"] += int(top1_checks["anchor_match"])
                    summary["top1_strict_passes"] += int(top1_pass)

                    top3_pass = False
                    for hit in docs[:3]:
                        ok, _checks = strict_match(case, hit)
                        if ok:
                            top3_pass = True
                            break
                    row["top3_strict_pass"] = top3_pass
                    summary["top3_strict_passes"] += int(top3_pass)

            except Exception as exc:
                row["error"] = str(exc)
                row["top1_strict_pass"] = False
                row["top3_strict_pass"] = False
                summary["errors"] += 1

            row["elapsed_sec"] = round(time.perf_counter() - case_start, 4)
            results.append(row)

            if i % progress_every == 0 or i == len(cases):
                print(
                    f"[{i}/{len(cases)}] top1_strict={summary['top1_strict_passes']} "
                    f"top3_strict={summary['top3_strict_passes']} errors={summary['errors']}"
                )

    elapsed = time.perf_counter() - started
    summary["elapsed_sec"] = round(elapsed, 3)
    summary["search_space_id"] = search_space_id
    summary["top_k"] = top_k
    summary["top1_strict_rate"] = round(100.0 * summary["top1_strict_passes"] / max(len(cases), 1), 2)
    summary["top3_strict_rate"] = round(100.0 * summary["top3_strict_passes"] / max(len(cases), 1), 2)
    summary["top1_thread_match_rate"] = round(100.0 * summary["top1_thread_match"] / max(len(cases), 1), 2)
    summary["top1_post_id_match_rate"] = round(100.0 * summary["top1_post_id_match"] / max(len(cases), 1), 2)
    summary["top1_anchor_match_rate"] = round(100.0 * summary["top1_anchor_match"] / max(len(cases), 1), 2)

    return {"summary": summary, "results": results}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run deterministic forum post retrieval tests against SurfSense retriever.")
    parser.add_argument("--cases", type=Path, required=True, help="Path to markdown test case file")
    parser.add_argument("--search-space-id", type=int, default=1, help="Search space ID to query")
    parser.add_argument("--top-k", type=int, default=5, help="Retriever top_k")
    parser.add_argument("--progress-every", type=int, default=10, help="Print progress every N cases")
    parser.add_argument("--output", type=Path, default=None, help="Output JSON path")
    parser.add_argument(
        "--exclude-title",
        action="append",
        default=[],
        help="Document title to ignore in retrieval candidates (repeatable)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cases = parse_cases(args.cases)
    if not cases:
        raise SystemExit("No test cases found")
    print(f"Loaded {len(cases)} cases from {args.cases}")

    report = asyncio.run(
        run_cases(
            cases=cases,
            search_space_id=args.search_space_id,
            top_k=args.top_k,
            progress_every=args.progress_every,
            exclude_titles=set(args.exclude_title),
        )
    )

    output_path = args.output
    if output_path is None:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output_path = Path(f"/app/scripts/forum_post_search_results_{ts}.json")
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    summary = report["summary"]
    print("\n=== SUMMARY ===")
    print(json.dumps(summary, indent=2))
    print(f"\nWrote report: {output_path}")


if __name__ == "__main__":
    main()
