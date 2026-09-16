#!/usr/bin/env python3
"""Fetch a WeChat Official Account article through OpenCLI and verify the artifact."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


BLOCK_MARKERS = (
    "当前环境异常",
    "环境异常",
    "完成验证后即可继续访问",
    "访问过于频繁",
    "verification required",
    "captcha",
    "安全验证",
)


def emit(payload: dict, exit_code: int) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(exit_code)


def normalize_url(raw: str) -> str:
    value = raw.strip().strip("\"'“”‘’")
    parts = urlsplit(value)
    if parts.scheme != "https" or parts.hostname != "mp.weixin.qq.com":
        emit(
            {
                "ok": False,
                "code": "invalid_url",
                "error": "只接受 https://mp.weixin.qq.com/ 的公众号文章链接。",
            },
            2,
        )
    return urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, ""))


def opencli_command() -> list[str] | None:
    for candidate in ("opencli", "opencli.cmd", "opencli.exe"):
        resolved = shutil.which(candidate)
        if resolved:
            resolved_path = Path(resolved)
            if os.name == "nt" and resolved_path.suffix.casefold() in {".cmd", ".bat", ".ps1"}:
                node = shutil.which("node.exe") or shutil.which("node")
                entrypoint = (
                    resolved_path.parent
                    / "node_modules"
                    / "@jackwener"
                    / "opencli"
                    / "dist"
                    / "src"
                    / "main.js"
                )
                if node and entrypoint.is_file():
                    return [node, str(entrypoint)]
            return [resolved]
    return None


def bridge_connected(command_prefix: list[str]) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            [*command_prefix, "profile", "list"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
            env=os.environ.copy(),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    transcript = "\n".join(part for part in (result.stdout, result.stderr) if part)
    connected = result.returncode == 0 and "No Browser Bridge profiles connected" not in transcript
    return connected, transcript[-2000:]


def snapshot_markdown(output_dir: Path) -> dict[Path, int]:
    return {
        path.resolve(): path.stat().st_mtime_ns
        for path in output_dir.rglob("*.md")
        if path.is_file()
    }


def candidate_files(output_dir: Path, before: dict[Path, int]) -> list[Path]:
    candidates: list[Path] = []
    for path in output_dir.rglob("*.md"):
        if not path.is_file():
            continue
        resolved = path.resolve()
        if resolved not in before or path.stat().st_mtime_ns > before[resolved]:
            candidates.append(resolved)
    return sorted(candidates, key=lambda path: path.stat().st_mtime_ns, reverse=True)


def verify_markdown(path: Path, source_url: str) -> tuple[bool, str]:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        return False, f"无法读取 Markdown：{exc}"

    folded = text.casefold()
    marker = next((item for item in BLOCK_MARKERS if item.casefold() in folded), None)
    if marker:
        return False, f"Markdown 命中验证页标记：{marker}"

    body = re.sub(r"^---\s.*?\s---\s*", "", text, flags=re.DOTALL)
    visible = re.sub(r"[#>*_`\[\]()!\-\s]", "", body)
    if len(visible) < 120:
        return False, "正文过短，无法确认已抓到原文。"

    if source_url not in text and "mp.weixin.qq.com" not in text:
        return False, "Markdown 没有保留微信公众号来源链接。"

    return True, "ok"


def classify_failure(output: str) -> tuple[str, str]:
    folded = output.casefold()
    if "extension" in folded and ("not connected" in folded or "unavailable" in folded):
        return "bridge_unavailable", "OpenCLI Chrome 扩展未连接。"
    if any(marker.casefold() in folded for marker in BLOCK_MARKERS):
        return "verification_required", "微信要求在 Chrome 中完成人工验证。"
    if "failed — verification required" in folded:
        return "verification_required", "微信要求在 Chrome 中完成人工验证。"
    return "fetch_failed", "OpenCLI 未生成可验证的原文 Markdown。"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch a public WeChat article as verified Markdown with local images."
    )
    parser.add_argument("url", help="A public https://mp.weixin.qq.com article URL")
    parser.add_argument(
        "--output",
        default=str(Path.cwd() / "公众号原文"),
        help="Output directory (default: ./公众号原文)",
    )
    parser.add_argument("--retries", type=int, default=3, help="Attempts, default 3")
    parser.add_argument(
        "--retry-delay", type=float, default=8.0, help="Seconds between attempts"
    )
    args = parser.parse_args()

    source_url = normalize_url(args.url)
    output_dir = Path(args.output).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    command_prefix = opencli_command()
    if not command_prefix:
        emit(
            {
                "ok": False,
                "code": "opencli_missing",
                "error": "没有找到 opencli。请安装 @jackwener/opencli。",
            },
            3,
        )

    connected, bridge_diagnostic = bridge_connected(command_prefix)
    if not connected:
        emit(
            {
                "ok": False,
                "verified_original": False,
                "code": "bridge_unavailable",
                "error": "OpenCLI Chrome 扩展未连接。请启用扩展后重试。",
                "diagnostic": bridge_diagnostic,
            },
            4,
        )

    attempts = max(1, min(args.retries, 5))
    before = snapshot_markdown(output_dir)
    transcripts: list[str] = []

    for attempt in range(1, attempts + 1):
        command = [
            *command_prefix,
            "weixin",
            "download",
            "--url",
            source_url,
            "--output",
            str(output_dir),
            "--download-images",
            "--window",
            "background",
            "--site-session",
            "persistent",
            "--keep-tab",
            "false",
            "--format",
            "json",
            "--trace",
            "retain-on-failure",
        ]
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=150,
                env=os.environ.copy(),
            )
            transcript = "\n".join(part for part in (result.stdout, result.stderr) if part)
        except subprocess.TimeoutExpired as exc:
            transcript = f"OpenCLI timeout: {exc}"
        transcripts.append(transcript[-4000:])

        for path in candidate_files(output_dir, before):
            verified, reason = verify_markdown(path, source_url)
            if not verified:
                transcripts.append(reason)
                continue
            image_dir = path.parent / "images"
            image_count = (
                sum(1 for image in image_dir.rglob("*") if image.is_file())
                if image_dir.exists()
                else 0
            )
            emit(
                {
                    "ok": True,
                    "verified_original": True,
                    "backend": "opencli-browser-bridge",
                    "source_url": source_url,
                    "markdown_path": str(path),
                    "image_count": image_count,
                    "bytes": path.stat().st_size,
                    "attempts": attempt,
                },
                0,
            )

        if attempt < attempts:
            time.sleep(max(1.0, min(args.retry_delay, 30.0)))

    combined = "\n".join(transcripts)
    code, error = classify_failure(combined)
    emit(
        {
            "ok": False,
            "verified_original": False,
            "code": code,
            "error": error,
            "source_url": source_url,
            "output_directory": str(output_dir),
            "attempts": attempts,
            "diagnostic": combined[-2000:],
        },
        4,
    )


if __name__ == "__main__":
    main()
