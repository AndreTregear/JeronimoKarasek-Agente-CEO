"""
LLM client for Agente-CEO — connects to local HPC AI services.
All inference stays local: encrypted SSH tunnels, no data leaves your network.

Services available on localhost (via SupercomputerReconnect mesh):
  - LLM:  localhost:18080 (Qwen3.5-122B, 262K context, OpenAI-compatible)
  - ASR:  localhost:18082 (Qwen3-ASR-1.7B, speech-to-text)
  - TTS:  localhost:18083 (Qwen3-TTS-1.7B, text-to-speech)
"""

import httpx
import json
import logging
from typing import Optional
from ..core.config import settings

logger = logging.getLogger("agente.llm")


class LLMClient:
    """OpenAI-compatible LLM client pointing to local HPC inference."""

    def __init__(self):
        self.base_url = settings.LLM_API_URL
        self.api_key = settings.LLM_API_KEY
        self.model = settings.LLM_MODEL
        self.headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

    async def chat(
        self,
        messages: list[dict],
        max_tokens: int = 2048,
        temperature: float = 0.7,
        system: str | None = None,
    ) -> str:
        """Send a chat completion request and return the response text."""
        if system:
            messages = [{"role": "system", "content": system}] + messages

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self.headers,
            )
            resp.raise_for_status()
            data = resp.json()

        choice = data["choices"][0]["message"]
        # Handle reasoning models that put content in reasoning_content
        return choice.get("content") or choice.get("reasoning_content", "")

    async def generate_json(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int = 4096,
    ) -> dict | list:
        """Generate structured JSON output from the LLM."""
        if not system:
            system = "You are a helpful assistant. Always respond with valid JSON only, no markdown or explanation."

        text = await self.chat(
            messages=[{"role": "user", "content": prompt}],
            system=system,
            max_tokens=max_tokens,
            temperature=0.3,
        )

        # Extract JSON from response (handle markdown code blocks)
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(text)


class ASRClient:
    """Speech-to-text using local Qwen3-ASR."""

    def __init__(self):
        self.base_url = settings.ASR_API_URL

    async def transcribe(self, audio_bytes: bytes, filename: str = "audio.wav", language: str = "auto") -> str:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.base_url}/v1/audio/transcriptions",
                files={"file": (filename, audio_bytes)},
                data={"language": language},
            )
            resp.raise_for_status()
            return resp.json()["text"]


class TTSClient:
    """Text-to-speech using local Qwen3-TTS."""

    def __init__(self):
        self.base_url = settings.TTS_API_URL

    async def synthesize(
        self,
        text: str,
        speaker: str = "ryan",
        language: str = "Auto",
        instruct: str = "",
    ) -> bytes:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.base_url}/v1/audio/speech",
                json={
                    "text": text,
                    "speaker": speaker,
                    "language": language,
                    "instruct": instruct,
                },
            )
            resp.raise_for_status()
            return resp.content


# Singleton instances
llm = LLMClient()
asr = ASRClient()
tts = TTSClient()
