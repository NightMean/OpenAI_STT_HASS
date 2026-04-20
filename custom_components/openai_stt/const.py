"""Constants for the OpenAI STT integration."""

DOMAIN = "openai_stt"

# Configuration keys
CONF_API_URL = "api_url"
CONF_MODEL = "model"
CONF_PROMPT = "prompt"
CONF_TEMPERATURE = "temperature"
CONF_REALTIME = "realtime"
CONF_NOISE_REDUCTION = "noise_reduction"

# Default values
DEFAULT_API_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "whisper-1"
DEFAULT_PROMPT = ""
DEFAULT_TEMPERATURE = 0.0
DEFAULT_REALTIME = False
DEFAULT_NOISE_REDUCTION = "none"

# Noise reduction options
NOISE_REDUCTION_OPTIONS = [
    "none",
    "near_field",
    "far_field",
]
