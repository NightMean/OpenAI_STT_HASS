# OpenAI-Compatible Speech-To-Text for Home Assistant

A Home Assistant custom integration for speech-to-text using any **OpenAI-compatible Whisper endpoint** — primarily designed for use with [**OlliteRT**](https://github.com/NightMean/ollitert), an on-device LLM server that runs Whisper models locally on Android.

Also works with OpenAI's hosted API and any other server that implements the [OpenAI Audio Transcription API](https://platform.openai.com/docs/api-reference/audio/createTranscription).

> **Fork lineage:** This is a fork of [georgesofianosgr/openai_stt_hass](https://github.com/georgesofianosgr/openai_stt_hass), which itself is a fork of [einToast/openai_stt_ha](https://github.com/einToast/openai_stt_ha). This fork adds support for custom model names, optional API keys, and is tailored for local/self-hosted STT servers.

## Features

- **Any OpenAI-compatible endpoint** — Point it at OlliteRT, OpenAI, LocalAI, Faster Whisper Server, or any compatible API
- **Auto-discover models** — Automatically fetches available models from your server's `/models` endpoint, with manual text input as fallback
- **Custom model names** — Enter any model name your server supports (e.g., `whisper-1`, `moonshine-base`, `whisper-large-v3`)
- **Optional API key** — No key required for local servers like OlliteRT
- **Full UI configuration** — Set up and manage everything through Home Assistant's UI
- **Multiple instances** — Create multiple STT entities with different servers/models
- **65+ language variants** — Broad language support via BCP 47 codes
- **Realtime API support** — OpenAI's streaming WebSocket transcription (beta)
- **Advanced options** — Prompt, temperature, and noise reduction settings

## Installation

### HACS (Custom Repository)

1. Open **HACS** in Home Assistant
2. Click the **three dots** (⋮) in the upper right → **Custom repositories**
3. Add: `https://github.com/NightMean/OpenAI_STT_HASS`
4. Select **Integration** as the category → **Add**
5. Find the integration and click **Download**
6. **Restart** Home Assistant

### Manual

1. Copy the `custom_components/openai_stt` directory into your Home Assistant `config/custom_components/` directory
2. **Restart** Home Assistant

## Configuration

### UI Setup (Recommended)

1. Go to **Settings** → **Devices & Services** → **+ Add Integration**
2. Search for **"OpenAI-Compatible Whisper STT"**
3. Fill in the setup form:

| Field | Required | Description |
|-------|----------|-------------|
| **API Key** | No | Leave empty for servers that don't require authentication (e.g., OlliteRT) |
| **API URL** | Yes | Base URL of your server (e.g., `http://192.168.1.100:8000/v1` for OlliteRT) |
| **Model Name** | Yes | The model to use — enter any name your server supports |
| **Name** | No | Friendly name for this STT instance |

4. Click **Submit**

After setup, click **Configure** on the integration card to adjust:
- Model name, prompt, temperature
- Realtime API mode (OpenAI only)
- Noise reduction (Realtime API only)

### Example: OlliteRT Setup

1. Install and start [OlliteRT](https://github.com/NightMean/ollitert) on your Android device
2. Load a Whisper model in OlliteRT
3. In Home Assistant, add the integration with:
   - **API Key:** *(leave empty)*
   - **API URL:** `http://<phone-ip>:8000/v1`
   - **Model Name:** The model name shown in OlliteRT (e.g., `whisper-1`)

### Example: OpenAI Setup

1. Get an API key from [platform.openai.com](https://platform.openai.com/api-keys)
2. Add the integration with:
   - **API Key:** Your OpenAI API key
   - **API URL:** `https://api.openai.com/v1` (default)
   - **Model Name:** `gpt-4o-mini-transcribe`, `gpt-4o-transcribe`, or `whisper-1`

### YAML Configuration (Legacy)

```yaml
stt:
  - platform: openai_stt
    api_key: YOUR_API_KEY  # optional for local servers
    api_url: http://192.168.1.100:8000/v1
    model: whisper-1
    # Optional
    prompt: ""
    temperature: 0
    realtime: false
    noise_reduction: null
```

### Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `api_key` | `""` | API key for authentication. Leave empty if not needed. |
| `api_url` | `https://api.openai.com/v1` | Base URL of the OpenAI-compatible API endpoint |
| `model` | `whisper-1` | Model name — any string your server accepts |
| `prompt` | `""` | Optional prompt to guide transcription |
| `temperature` | `0.0` | Sampling temperature (0–1). Lower = more deterministic. |
| `realtime` | `false` | Use OpenAI Realtime WebSocket API (OpenAI only) |
| `noise_reduction` | `none` | `none`, `near_field`, or `far_field` (Realtime API only) |

## Troubleshooting

1. **Can't connect** — Verify the API URL is reachable from your Home Assistant instance. For OlliteRT, ensure the phone and HA are on the same network.
2. **Authentication errors** — Check your API key. For local servers without auth, make sure the API key field is empty.
3. **No transcription results** — Verify the model name matches what your server offers. Check HA logs for details.
4. **Check logs** — Go to **Settings** → **System** → **Logs** and filter for `openai_stt`.

## License

Apache 2.0 — see [LICENSE](LICENSE) for details.
