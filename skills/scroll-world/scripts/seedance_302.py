#!/usr/bin/env python3
"""Create, poll, and download 302.AI Seedance 2.0 video tasks."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
from pathlib import Path
import sys
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_BASE_URL = "https://api.302.ai"
DEFAULT_MODEL = "doubao-seedance-2-0-260128"
TASK_PATH = "/volcengine/api/v3/contents/generations/tasks"
TERMINAL_SUCCESS = {"succeeded", "completed", "success"}
TERMINAL_FAILURE = {"failed", "error", "cancelled", "canceled", "blocked", "expired"}


class AdapterError(RuntimeError):
    """A safe-to-display adapter error."""


def request_json(
    method: str, url: str, api_key: str, payload: dict[str, Any] | None = None
) -> tuple[int, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=60) as response:
            raw = response.read().decode("utf-8", errors="replace")
            return response.status, json.loads(raw) if raw.strip() else {}
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            detail = {"message": raw[:2000]}
        safe_detail = json.dumps(detail, ensure_ascii=False).replace(api_key, "[REDACTED]")
        raise AdapterError(f"302.AI HTTP {exc.code}: {safe_detail[:4000]}") from None
    except URLError as exc:
        raise AdapterError(f"302.AI connection failed: {exc.reason}") from None


def frame_data_url(path: Path) -> str:
    if not path.is_file():
        raise AdapterError(f"Frame file not found: {path}")
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    if not mime.startswith("image/"):
        raise AdapterError(f"Frame must be an image: {path}")
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def nested_value(data: Any, paths: tuple[tuple[str, ...], ...]) -> Any:
    for path in paths:
        value = data
        for key in path:
            if not isinstance(value, dict) or key not in value:
                break
            value = value[key]
        else:
            if value not in (None, ""):
                return value
    return None


def task_id_from(data: Any) -> str:
    value = nested_value(
        data,
        (("id",), ("task_id",), ("data", "id"), ("data", "task_id"), ("result", "id")),
    )
    if not value:
        raise AdapterError(f"Creation response has no task id: {json.dumps(data, ensure_ascii=False)[:2000]}")
    return str(value)


def status_from(data: Any) -> str:
    value = nested_value(data, (("status",), ("data", "status"), ("result", "status")))
    return str(value or "unknown").lower()


def video_url_from(data: Any) -> str | None:
    value = nested_value(
        data,
        (
            ("content", "video_url"),
            ("data", "content", "video_url"),
            ("result", "content", "video_url"),
            ("video_url",),
            ("data", "video_url"),
        ),
    )
    return str(value) if value else None


def create_payload(args: argparse.Namespace) -> dict[str, Any]:
    prompt = args.prompt or args.prompt_file.read_text(encoding="utf-8")
    content: list[dict[str, Any]] = [{"type": "text", "text": prompt.strip()}]
    content.append(
        {
            "type": "image_url",
            "image_url": {"url": frame_data_url(args.first_frame)},
            "role": "first_frame",
        }
    )
    if args.last_frame:
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": frame_data_url(args.last_frame)},
                "role": "last_frame",
            }
        )
    return {
        "model": args.model,
        "content": content,
        "resolution": args.resolution,
        "duration": args.duration,
        "ratio": args.ratio,
        "generate_audio": args.audio,
        "watermark": args.watermark,
    }


def poll_task(base_url: str, api_key: str, task_id: str, interval: float, timeout: float) -> Any:
    deadline = time.monotonic() + timeout
    while True:
        _, data = request_json("GET", f"{base_url}{TASK_PATH}/{task_id}", api_key)
        status = status_from(data)
        print(f"task={task_id} status={status}", file=sys.stderr, flush=True)
        if status in TERMINAL_SUCCESS:
            return data
        if status in TERMINAL_FAILURE:
            raise AdapterError(f"Task {task_id} ended with status {status}: {json.dumps(data, ensure_ascii=False)[:3000]}")
        if time.monotonic() >= deadline:
            raise AdapterError(f"Timed out waiting for task {task_id} after {timeout:g}s")
        time.sleep(interval)


def download(url: str, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_name(f".{output.name}.part")
    try:
        with urlopen(Request(url, headers={"Accept": "video/mp4"}), timeout=120) as response:
            with temp.open("wb") as target:
                while chunk := response.read(1024 * 1024):
                    target.write(chunk)
        if temp.stat().st_size == 0:
            raise AdapterError("Downloaded video is empty")
        temp.replace(output)
    except (HTTPError, URLError, OSError) as exc:
        temp.unlink(missing_ok=True)
        raise AdapterError(f"Video download failed: {exc}") from None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--prompt", help="Video prompt text")
    source.add_argument("--prompt-file", type=Path, help="UTF-8 prompt file")
    parser.add_argument("--first-frame", type=Path, help="Local first-frame image")
    parser.add_argument("--last-frame", type=Path, help="Optional local last-frame image")
    parser.add_argument("--output", type=Path, help="Downloaded MP4 destination")
    parser.add_argument("--task-id", help="Poll an existing task instead of creating one")
    parser.add_argument("--submit-only", action="store_true", help="Create and print the task id without polling")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--ratio", default="16:9")
    parser.add_argument("--duration", type=int, default=5)
    parser.add_argument("--resolution", choices=("480p", "720p", "1080p"), default="1080p")
    parser.add_argument("--audio", action="store_true", help="Request generated audio (off by default)")
    parser.add_argument("--watermark", action="store_true", help="Request a watermark (off by default)")
    parser.add_argument("--poll-interval", type=float, default=8.0)
    parser.add_argument("--timeout", type=float, default=1800.0)
    args = parser.parse_args()
    if not args.task_id and (not (args.prompt or args.prompt_file) or not args.first_frame):
        parser.error("creation requires a prompt and --first-frame")
    if args.task_id and args.submit_only:
        parser.error("--task-id and --submit-only cannot be combined")
    if not args.submit_only and not args.output:
        parser.error("--output is required unless --submit-only is used")
    if args.duration <= 0 or args.poll_interval <= 0 or args.timeout <= 0:
        parser.error("duration, poll interval, and timeout must be positive")
    return args


def main() -> int:
    args = parse_args()
    api_key = os.environ.get("AI302_API_KEY", "")
    if not api_key:
        raise AdapterError("AI302_API_KEY is missing")
    base_url = os.environ.get("AI302_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    if args.task_id:
        task_id = args.task_id
    else:
        _, created = request_json("POST", f"{base_url}{TASK_PATH}", api_key, create_payload(args))
        task_id = task_id_from(created)
        print(task_id)
        if args.submit_only:
            return 0
    result = poll_task(base_url, api_key, task_id, args.poll_interval, args.timeout)
    video_url = video_url_from(result)
    if not video_url:
        raise AdapterError(f"Successful task {task_id} has no video URL")
    download(video_url, args.output)
    print(f"saved={args.output}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AdapterError, OSError, UnicodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
