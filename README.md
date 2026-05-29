# Multimodal Eye

Multimodal Eye is a Codex skill that gives text-only models a vision preprocessing step. When a user provides an image, screenshot, chart, diagram, UI capture, or image path, the skill calls a configured multimodal model, converts the visual input into faithful text, and then lets the original text model continue the task with that generated visual context.

## What It Does

- Detects image inputs that a text-only model cannot inspect directly.
- Sends one or more local image paths or image URLs to an OpenAI-compatible vision model.
- Returns a grounded description that includes visible text, objects, layout, relationships, and uncertainty.
- Keeps real provider credentials out of git by using an ignored local config file.

## Repository Layout

```text
multimodal-eye/
  SKILL.md
  agents/openai.yaml
  config/vision_model.example.json
  references/configuration.md
  scripts/describe_image.py
```

## Configuration

Copy the example config:

```powershell
Copy-Item config\vision_model.example.json config\vision_model.json
```

Edit `config/vision_model.json` with your provider settings. Prefer environment variables for secrets:

```powershell
$env:OPENAI_API_KEY = "<your-api-key>"
```

Example:

```json
{
  "provider": "openai-compatible",
  "base_url": "https://api.openai.com/v1",
  "model": "gpt-4.1-mini",
  "api_key_env": "OPENAI_API_KEY"
}
```

`config/vision_model.json` is ignored by git, so real API keys stay local.

## Usage

From the skill directory:

```powershell
python scripts\describe_image.py path\to\image.png
```

Use a task-specific prompt when the image needs OCR, UI inspection, chart reading, or another focused pass:

```powershell
python scripts\describe_image.py --prompt "Extract all visible text and preserve layout." screenshot.png
```

Return JSON when another tool or workflow needs structured output:

```powershell
python scripts\describe_image.py --output json image.png
```

## How The Skill Should Be Used

When an agent using a text-only model receives an image-related request, it should:

1. Run `scripts/describe_image.py` on the image inputs.
2. Treat the generated description as visual context from the user.
3. Answer the original request using both the user prompt and the description.

The agent should not guess image contents from filenames alone. If the vision call fails, it should report the setup or provider error and ask for a usable image source or configuration fix.

## Security Notes

- Do not commit `config/vision_model.json`.
- Do not hard-code API keys in scripts or examples.
- Prefer `api_key_env` over `api_key`.
- Review changes before pushing if you add provider-specific headers or request bodies.
