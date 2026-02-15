#!/usr/bin/env python3
"""
Headless UI streaming check (Playwright).

Purpose: validate that the SurfSense UI renders intermediate streaming updates
(thinking steps / partial assistant output) while the model is still generating.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time

from playwright.async_api import async_playwright


def _ms(delta_s: float) -> int:
    return int(delta_s * 1000)


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://frontend:3000")
    ap.add_argument("--email", required=True)
    ap.add_argument("--password", required=True)
    ap.add_argument("--search-space-id", type=int, default=3)
    ap.add_argument("--thread-id", type=int, default=308)
    ap.add_argument(
        "--prompt",
        default="Give a 2 sentence summary of what this chat is about.",
    )
    ap.add_argument("--timeout-ms", type=int, default=60_000)
    args = ap.parse_args()

    base_url = args.base_url.rstrip("/")
    timeout = args.timeout_ms

    console_lines: list[str] = []
    page_errors: list[str] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 720})
        page = await context.new_page()

        page.on("console", lambda m: console_lines.append(f"[{m.type}] {m.text}"))
        page.on("pageerror", lambda e: page_errors.append(str(e)))

        t0 = time.monotonic()
        await page.goto(f"{base_url}/login", wait_until="domcontentloaded", timeout=timeout)

        await page.fill("#email", args.email, timeout=timeout)
        await page.fill("#password", args.password, timeout=timeout)

        # Submit local login form.
        await page.click("form button[type=submit]", timeout=timeout)

        # TokenHandler on /auth/callback stores tokens into localStorage.
        await page.wait_for_function(
            "() => !!localStorage.getItem('surfsense_bearer_token')",
            timeout=timeout,
        )
        t_login = time.monotonic()

        thread_url = f"{base_url}/dashboard/{args.search_space_id}/new-chat/{args.thread_id}"
        await page.goto(thread_url, wait_until="domcontentloaded", timeout=timeout)

        # Wait for the composer to become ready.
        await page.wait_for_selector("button[aria-label='Send message']", timeout=timeout)
        await page.wait_for_selector(
            "div[role='textbox'][aria-label='Message input with inline mentions']",
            timeout=timeout,
        )

        # Send message.
        await page.click(
            "div[role='textbox'][aria-label='Message input with inline mentions']",
            timeout=timeout,
        )
        await page.keyboard.type(args.prompt, delay=5)

        t_send = time.monotonic()
        await page.click("button[aria-label='Send message']", timeout=timeout)

        # Expect: stop button becomes visible quickly.
        await page.wait_for_selector("button[aria-label='Stop generating']", timeout=10_000)
        t_stop_visible = time.monotonic()

        # Expect: thinking steps header appears during streaming.
        # (We match multiple possible step titles to avoid brittleness.)
        thinking_re = re.compile(
            r"(Understanding your request|Processing\s+\d+/\d+\s+steps|Reading your content)"
        )
        thinking_pat_js = json.dumps(thinking_re.pattern)
        await page.wait_for_function(
            f"() => new RegExp({thinking_pat_js}).test(document.body?.innerText || '')",
            timeout=10_000,
        )
        t_thinking_visible = time.monotonic()

        # Expect: assistant text begins to appear before completion.
        await page.wait_for_function(
            """() => {
              const nodes = Array.from(document.querySelectorAll('.aui-assistant-message-content'));
              const txt = nodes.map(n => n.textContent || '').join('\\n').trim();
              return txt.length > 0;
            }""",
            timeout=20_000,
        )
        t_first_text = time.monotonic()

        # Wait for completion (send button returns).
        await page.wait_for_selector("button[aria-label='Send message']", timeout=timeout)
        t_done = time.monotonic()

        await context.close()
        await browser.close()

    report = {
        "base_url": base_url,
        "thread_url": thread_url,
        "prompt": args.prompt,
        "t_login_ms": _ms(t_login - t0),
        "t_stop_button_ms": _ms(t_stop_visible - t_send),
        "t_thinking_visible_ms": _ms(t_thinking_visible - t_send),
        "t_first_text_ms": _ms(t_first_text - t_send),
        "t_done_ms": _ms(t_done - t_send),
        "console_lines": len(console_lines),
        "page_errors": len(page_errors),
    }
    print(json.dumps(report, ensure_ascii=True))
    if page_errors:
        print("\nPage errors (first 5):")
        for line in page_errors[:5]:
            print(line)
    if console_lines:
        # Only print errors/warns to avoid noise.
        bad = [l for l in console_lines if l.startswith("[error]") or l.startswith("[warning]")]
        if bad:
            print("\nConsole warnings/errors (first 20):")
            for line in bad[:20]:
                print(line)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(__import__("asyncio").run(main()))
    except KeyboardInterrupt:
        raise SystemExit(130)
