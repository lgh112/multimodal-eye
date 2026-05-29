---
name: multimodal-eye
description: Give text-only or non-vision models a vision preprocessing step by calling a configured multimodal model to describe attached images, screenshots, diagrams, UI captures, photos, charts, or local image paths before continuing with the user's original request. Use when the user includes image inputs or asks to inspect, identify, OCR, compare, summarize, reason about, or extract information from an image and the active model cannot directly process images.
---

# Multimodal Eye

## Workflow

Use this skill as an image-to-text adapter before answering the user's real request.

1. Detect image inputs: attached images, screenshot references, local image paths, or URLs that point to images.
2. Check configuration before the first call. Read `references/configuration.md` if setup is missing or unclear.
3. Run `scripts/describe_image.py` with every image that should inform the answer.
4. Treat the script output as the visual context supplied by the user.
5. Continue the original task using both the user's prompt and the generated image description.

Do not answer visual questions from filenames alone. If the script cannot inspect the image, state the failure and ask for a usable image path, URL, or configuration fix.

## Quick Start

From the skill directory:

```powershell
python scripts/describe_image.py path\to\image.png
```

When Python is not on `PATH`, use the runtime available in the host environment. In Codex Desktop, `codex_app.load_workspace_dependencies` can reveal the bundled Python executable.

The script reads configuration from `config/vision_model.json` by default. To use another file:

```powershell
python scripts/describe_image.py --config C:\path\to\vision_model.json path\to\image.png
```

## Output Contract

Ask the vision model for compact, faithful observations. Prefer grounded details over guesses:

- visible objects, people, UI elements, text, labels, chart axes, and layout
- relationships and spatial arrangement
- uncertainty or unreadable regions
- safety-relevant or task-relevant caveats

When the user needs OCR, charts, tables, or UI debugging, pass a task-specific prompt with `--prompt` so the description emphasizes the needed evidence.

## Configuration

Keep real credentials out of git. Copy `config/vision_model.example.json` to `config/vision_model.json`, then set either `api_key_env` or `api_key`.

Prefer environment variables for API keys. `config/vision_model.json` is ignored by git.

Read `references/configuration.md` for supported fields and provider notes.

## Failure Handling

If configuration is missing, invalid, or the provider returns an error:

1. Do not invent image contents.
2. Report the specific setup or API failure without exposing secrets.
3. Ask the user to fix the configuration or provide a different image source.

If only some images succeed, use the successful descriptions and clearly identify which images could not be inspected.
