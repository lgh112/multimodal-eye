# Multimodal Eye Configuration

Copy `config/vision_model.example.json` to `config/vision_model.json` and edit the copy. The real config is ignored by git so secrets do not enter version control.

## Required Fields

- `provider`: Use `openai-compatible`.
- `model`: Vision-capable model name for your provider.
- `api_key_env` or `api_key`: Prefer `api_key_env`, such as `OPENAI_API_KEY`.

Provide either:

- `base_url`: API root, such as `https://api.openai.com/v1`; the script appends `/chat/completions`.
- `endpoint`: Full chat completions endpoint. Use this when a provider has a nonstandard path.

## Optional Fields

- `temperature`: Defaults to `0`.
- `max_tokens`: Defaults to `1200`.
- `timeout_seconds`: Defaults to `60`.
- `detail`: Passed to `image_url.detail` when supported by the provider.
- `system_prompt`: System message for the vision model.
- `default_prompt`: Vision instruction used when `--prompt` is not passed.
- `headers`: Extra HTTP headers for provider-specific requirements.
- `extra_body`: Extra JSON body fields merged into the request.

## Recommended Setup

Use an environment variable for the API key:

```powershell
$env:OPENAI_API_KEY = "sk-..."
```

Then create:

```json
{
  "provider": "openai-compatible",
  "base_url": "https://api.openai.com/v1",
  "model": "gpt-4.1-mini",
  "api_key_env": "OPENAI_API_KEY"
}
```

For another OpenAI-compatible provider, set `base_url` or `endpoint`, choose a vision-capable model, and keep the same message format unless the provider documents otherwise.
