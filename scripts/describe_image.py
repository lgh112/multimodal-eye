#!/usr/bin/env python3
"""Describe images with an OpenAI-compatible multimodal chat API."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_PROMPT = (
    "Describe the image for a text-only model. Be faithful and concise. "
    "Include visible text, important objects, layout, relationships, and "
    "uncertainties. Do not speculate beyond the visual evidence."
)


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_config_path() -> Path:
    env_path = os.environ.get("MULTIMODAL_EYE_CONFIG")
    if env_path:
        return Path(env_path).expanduser()
    return skill_root() / "config" / "vision_model.json"


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        example = skill_root() / "config" / "vision_model.example.json"
        raise SystemExit(
            f"Config not found: {path}\n"
            f"Copy {example} to {path} and fill in the provider settings."
        )
    try:
        with path.open("r", encoding="utf-8") as handle:
            config = json.load(handle)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON config {path}: {exc}") from exc

    if not isinstance(config, dict):
        raise SystemExit("Config must be a JSON object.")
    return config


def require_string(config: dict[str, Any], key: str) -> str:
    value = config.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SystemExit(f"Config field '{key}' must be a non-empty string.")
    return value.strip()


def resolve_api_key(config: dict[str, Any]) -> str:
    env_name = config.get("api_key_env")
    if isinstance(env_name, str) and env_name.strip():
        api_key = os.environ.get(env_name.strip())
        if api_key:
            return api_key
        raise SystemExit(f"Environment variable '{env_name.strip()}' is not set.")

    api_key = config.get("api_key")
    if isinstance(api_key, str) and api_key.strip():
        return api_key.strip()

    raise SystemExit("Set either 'api_key_env' or 'api_key' in the config.")


def resolve_endpoint(config: dict[str, Any]) -> str:
    endpoint = config.get("endpoint")
    if isinstance(endpoint, str) and endpoint.strip():
        return endpoint.strip().rstrip("/")

    base_url = require_string(config, "base_url").rstrip("/")
    return f"{base_url}/chat/completions"


def image_content(image_ref: str, detail: str | None) -> dict[str, Any]:
    if image_ref.startswith(("http://", "https://")):
        url = image_ref
    else:
        path = Path(image_ref).expanduser()
        if not path.exists():
            raise SystemExit(f"Image not found: {image_ref}")
        mime_type, _ = mimetypes.guess_type(str(path))
        if not mime_type or not mime_type.startswith("image/"):
            mime_type = "image/png"
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        url = f"data:{mime_type};base64,{encoded}"

    image_url: dict[str, Any] = {"url": url}
    if detail:
        image_url["detail"] = detail
    return {"type": "image_url", "image_url": image_url}


def request_description(
    config: dict[str, Any],
    images: list[str],
    prompt: str,
) -> dict[str, Any]:
    model = require_string(config, "model")
    endpoint = resolve_endpoint(config)
    api_key = resolve_api_key(config)
    detail = config.get("detail")
    if detail is not None and not isinstance(detail, str):
        raise SystemExit("Config field 'detail' must be a string when provided.")

    content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
    content.extend(image_content(image, detail) for image in images)

    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": config.get(
                    "system_prompt",
                    "You are a careful visual description assistant.",
                ),
            },
            {"role": "user", "content": content},
        ],
        "temperature": float(config.get("temperature", 0)),
        "max_tokens": int(config.get("max_tokens", 1200)),
    }

    extra_body = config.get("extra_body")
    if isinstance(extra_body, dict):
        payload.update(extra_body)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    extra_headers = config.get("headers")
    if isinstance(extra_headers, dict):
        headers.update({str(key): str(value) for key, value in extra_headers.items()})

    data = json.dumps(payload).encode("utf-8")
    timeout = int(config.get("timeout_seconds", 60))
    request = urllib.request.Request(endpoint, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Vision provider HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Vision provider request failed: {exc.reason}") from exc
    except TimeoutError as exc:
        raise SystemExit("Vision provider request timed out.") from exc


def extract_text(response: dict[str, Any]) -> str:
    try:
        content = response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise SystemExit(
            "Provider response did not contain choices[0].message.content."
        ) from exc

    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "\n".join(parts).strip()
    raise SystemExit("Provider response content was not text.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Describe images using a configured multimodal model."
    )
    parser.add_argument("images", nargs="+", help="Local image paths or image URLs.")
    parser.add_argument(
        "--config",
        default=str(default_config_path()),
        help="Path to vision_model.json. Defaults to config/vision_model.json.",
    )
    parser.add_argument(
        "--prompt",
        default=None,
        help="Task-specific instruction for the vision model.",
    )
    parser.add_argument(
        "--output",
        choices=("text", "json"),
        default="text",
        help="Output only the description text or a JSON wrapper.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).expanduser()
    config = load_config(config_path)
    prompt = args.prompt or config.get("default_prompt") or DEFAULT_PROMPT
    if not isinstance(prompt, str) or not prompt.strip():
        raise SystemExit("Prompt must be a non-empty string.")

    response = request_description(config, args.images, prompt.strip())
    description = extract_text(response)
    if args.output == "json":
        print(
            json.dumps(
                {
                    "images": args.images,
                    "model": config.get("model"),
                    "description": description,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(description)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
