"""HTTP client for OpenAI STT."""

from __future__ import annotations

from collections.abc import AsyncIterable
import io
import logging
import time
import wave

from aiohttp import ClientError, ClientResponseError, FormData

from homeassistant.components.stt import SpeechMetadata, SpeechResult, SpeechResultState

_LOGGER = logging.getLogger(__name__)


def _convert_language_code(language: str) -> str:
    """Convert BCP 47 language code to ISO 639-1 code for OpenAI API.

    Home Assistant uses BCP 47 (e.g., 'en-US'), but OpenAI expects ISO 639-1 (e.g., 'en').
    Special handling for Chinese: zh-CN -> zh, zh-TW -> zh
    """
    if "-" in language:
        return language.split("-")[0]
    return language


class OpenAIHTTPClient:
    """HTTP client for OpenAI STT API."""

    def __init__(
        self,
        client,
        api_key: str,
        api_url: str,
        model: str,
        prompt: str,
        temperature: float,
    ) -> None:
        """Initialize the HTTP client."""
        self.client = client
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        self.prompt = prompt
        self.temperature = temperature

    async def _collect_audio_data(self, stream: AsyncIterable[bytes]) -> bytes:
        """Collect all audio data from the stream."""
        audio_data = b""
        async for chunk in stream:
            audio_data += chunk
        _LOGGER.debug("Audio data size: %d bytes", len(audio_data))
        return audio_data

    def _convert_to_wav(self, metadata: SpeechMetadata, audio_data: bytes) -> bytes:
        """Convert raw audio data to WAV format."""
        wav_stream = io.BytesIO()
        with wave.open(wav_stream, "wb") as wf:
            wf.setnchannels(metadata.channel)
            wf.setsampwidth(metadata.bit_rate // 8)
            wf.setframerate(metadata.sample_rate)
            wf.writeframes(audio_data)
        return wav_stream.getvalue()

    def _prepare_request_data(
        self, language: str, wav_data: bytes
    ) -> tuple[dict, FormData]:
        """Prepare headers and form data for the API request."""
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        # Convert BCP 47 language code to ISO 639-1 for OpenAI API
        openai_language = _convert_language_code(language)

        form = FormData()
        form.add_field(
            "file", wav_data, filename="whisper_audio.wav", content_type="audio/wav"
        )
        form.add_field("model", self.model)
        form.add_field("language", openai_language)
        form.add_field("prompt", self.prompt)
        form.add_field("temperature", str(self.temperature))
        form.add_field("response_format", "json")

        _LOGGER.debug(
            "Preparing request to API with parameters: model=%s, language=%s (converted to %s), prompt=%s, temperature=%s",
            self.model,
            language,
            openai_language,
            self.prompt,
            self.temperature,
        )

        return headers, form

    async def _send_request(
        self,
        url: str,
        headers: dict,
        form: FormData,
    ) -> SpeechResult:
        """Send HTTP request to the API and process the response."""
        try:
            start_time = time.perf_counter()

            response = await self.client.post(
                url,
                headers=headers,
                data=form,
                timeout=10,
            )
            response.raise_for_status()
            result = await response.json()
            _LOGGER.debug("API response: %s", result)

            duration = time.perf_counter() - start_time
            _LOGGER.debug("Transcription duration: %.2f seconds", duration)

            final_text = result.get("text", "").strip()

            _LOGGER.debug("Transcription result: %s", final_text)

            if not final_text:
                _LOGGER.warning("HTTP transcription resulted in empty text")
                return SpeechResult("", SpeechResultState.SUCCESS)

            return SpeechResult(final_text, SpeechResultState.SUCCESS)

        except ClientError as err:
            if isinstance(err, ClientResponseError):
                error_msg = f"HTTP {err.status}"
                if err.message:
                    error_msg += f": {err.message}"
                _LOGGER.error("%s - %s", error_msg, err.request_info.url)
            else:
                _LOGGER.error("HTTP error: %s", err)
            return SpeechResult("", SpeechResultState.ERROR)
        except Exception:
            _LOGGER.exception("Error sending audio")
            return SpeechResult("", SpeechResultState.ERROR)

    async def async_process_audio_stream(
        self, metadata: SpeechMetadata, stream: AsyncIterable[bytes]
    ) -> SpeechResult:
        """Process audio stream via HTTP POST to OpenAI Transcription API."""

        # Collect and convert audio data
        audio_data = await self._collect_audio_data(stream)
        wav_data = self._convert_to_wav(metadata, audio_data)

        # Prepare request data
        headers, form = self._prepare_request_data(metadata.language, wav_data)

        # Send request and get response
        url = f"{self.api_url}/audio/transcriptions"
        _LOGGER.debug("Sending request to API: %s", url)

        return await self._send_request(url, headers, form)
