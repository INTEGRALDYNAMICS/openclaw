#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Any

import soundfile as sf
import torch
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field
from qwen_tts import Qwen3TTSModel


def _env(name: str, default: str) -> str:
    value = os.environ.get(name)
    return value.strip() if isinstance(value, str) and value.strip() else default


def _env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _to_dtype(value: str) -> torch.dtype:
    normalized = value.strip().lower()
    mapping = {
        "fp16": torch.float16,
        "float16": torch.float16,
        "bf16": torch.bfloat16,
        "bfloat16": torch.bfloat16,
        "fp32": torch.float32,
        "float32": torch.float32,
    }
    if normalized not in mapping:
        raise ValueError(f"Unsupported dtype: {value}")
    return mapping[normalized]


def _normalize_speaker(speaker: str) -> str:
    return speaker.strip().lower()


def _encode_audio(tmp_dir: Path, wav: Any, sample_rate: int, response_format: str) -> tuple[bytes, str]:
    in_wav = tmp_dir / "input.wav"
    sf.write(str(in_wav), wav, sample_rate)

    fmt = response_format.strip().lower()
    if fmt == "opus":
        out_file = tmp_dir / "output.ogg"
        cmd = [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(in_wav),
            "-ac",
            "1",
            "-ar",
            "48000",
            "-c:a",
            "libopus",
            "-b:a",
            "64k",
            str(out_file),
        ]
        content_type = "audio/ogg"
    elif fmt == "mp3":
        out_file = tmp_dir / "output.mp3"
        cmd = [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(in_wav),
            "-ac",
            "1",
            "-ar",
            "24000",
            "-c:a",
            "libmp3lame",
            "-b:a",
            "128k",
            str(out_file),
        ]
        content_type = "audio/mpeg"
    elif fmt == "pcm":
        out_file = tmp_dir / "output.pcm"
        cmd = [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(in_wav),
            "-ac",
            "1",
            "-ar",
            "24000",
            "-f",
            "s16le",
            str(out_file),
        ]
        content_type = "application/octet-stream"
    elif fmt == "wav":
        out_file = tmp_dir / "output.wav"
        cmd = [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(in_wav),
            "-ac",
            "1",
            "-ar",
            "24000",
            str(out_file),
        ]
        content_type = "audio/wav"
    else:
        raise ValueError(f"Unsupported response_format: {response_format}")

    subprocess.run(cmd, check=True)
    return out_file.read_bytes(), content_type


class SpeechRequest(BaseModel):
    model: str | None = None
    input: str = Field(..., min_length=1)
    voice: str | None = None
    response_format: str = "mp3"


class QwenTtsRuntime:
    def __init__(self) -> None:
        self.model_id = _env("QWEN_TTS_MODEL", "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice")
        self.device = _env("QWEN_TTS_DEVICE", "cpu")
        self.primary_dtype_name = _env("QWEN_TTS_DTYPE", "fp16")
        self.fallback_dtype_name = _env("QWEN_TTS_FALLBACK_DTYPE", "bf16")
        self.language = _env("QWEN_TTS_LANGUAGE", "Spanish")
        self.default_speaker = _env("QWEN_TTS_DEFAULT_SPEAKER", "serena")
        self.personality = _env(
            "QWEN_TTS_PERSONALITY",
            "Tone: cyberpunk calm, playful, precise, warm confidence.",
        )
        self.max_input_chars = _env_int("QWEN_TTS_MAX_INPUT_CHARS", 380)
        self.api_key = _env("QWEN_TTS_API_KEY", "")

        self._lock = threading.Lock()
        self._current_dtype_name = self.primary_dtype_name
        self._model = self._load(self.primary_dtype_name)
        self._speakers = self._resolve_speakers()

    def _load(self, dtype_name: str) -> Qwen3TTSModel:
        dtype = _to_dtype(dtype_name)
        print(f"[qwen3-tts] loading model={self.model_id} device={self.device} dtype={dtype_name}")
        model = Qwen3TTSModel.from_pretrained(
            self.model_id,
            device_map=self.device,
            dtype=dtype,
        )
        print(f"[qwen3-tts] ready dtype={dtype_name}")
        self._current_dtype_name = dtype_name
        return model

    def _resolve_speakers(self) -> dict[str, str]:
        getter = getattr(self._model.model, "get_supported_speakers", None)
        if not callable(getter):
            return {}
        raw = getter() or []
        speakers = list(raw)
        return {_normalize_speaker(name): name for name in speakers}

    def _pick_speaker(self, requested: str | None) -> str:
        if not self._speakers:
            return requested or self.default_speaker
        if requested:
            key = _normalize_speaker(requested)
            if key in self._speakers:
                return self._speakers[key]
        default_key = _normalize_speaker(self.default_speaker)
        if default_key in self._speakers:
            return self._speakers[default_key]
        return next(iter(self._speakers.values()))

    def _should_retry_bf16(self, err: Exception) -> bool:
        if self._current_dtype_name not in {"fp16", "float16"}:
            return False
        message = str(err).lower()
        return "nan" in message or "inf" in message or "probability tensor" in message

    def _maybe_reload_fallback(self) -> None:
        if self.fallback_dtype_name == self._current_dtype_name:
            return
        self._model = self._load(self.fallback_dtype_name)
        self._speakers = self._resolve_speakers()

    def synthesize(self, text: str, speaker_hint: str | None) -> tuple[Any, int, str]:
        clipped = text.strip()
        if len(clipped) > self.max_input_chars:
            clipped = clipped[: self.max_input_chars - 1].rstrip() + "…"

        speaker = self._pick_speaker(speaker_hint)
        instruct = self.personality.strip() or None

        with self._lock:
            try:
                wavs, sr = self._model.generate_custom_voice(
                    text=clipped,
                    language=self.language,
                    speaker=speaker,
                    instruct=instruct,
                )
                return wavs[0], sr, speaker
            except Exception as err:
                if self._should_retry_bf16(err):
                    print(f"[qwen3-tts] fp16 unstable; switching to {self.fallback_dtype_name}: {err}")
                    self._maybe_reload_fallback()
                    wavs, sr = self._model.generate_custom_voice(
                        text=clipped,
                        language=self.language,
                        speaker=speaker,
                        instruct=instruct,
                    )
                    return wavs[0], sr, speaker
                raise


runtime = QwenTtsRuntime()
app = FastAPI(title="qwen3-tts-openai-compat")


@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse(
        {
            "ok": True,
            "model": runtime.model_id,
            "dtype": runtime._current_dtype_name,
            "defaultSpeaker": runtime.default_speaker,
            "availableSpeakers": list(runtime._speakers.values()),
            "language": runtime.language,
            "maxInputChars": runtime.max_input_chars,
        }
    )


@app.post("/v1/audio/speech")
def create_speech(payload: SpeechRequest, authorization: str | None = Header(default=None)) -> Response:
    if runtime.api_key:
        bearer = f"Bearer {runtime.api_key}"
        if authorization != bearer:
            raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        wav, sr, speaker = runtime.synthesize(payload.input, payload.voice)
        with tempfile.TemporaryDirectory(prefix="qwen3tts-") as td:
            audio_bytes, content_type = _encode_audio(
                Path(td), wav, sr, payload.response_format
            )
        headers = {
            "x-qwen-speaker": speaker,
            "x-qwen-dtype": runtime._current_dtype_name,
        }
        return Response(content=audio_bytes, media_type=content_type, headers=headers)
    except HTTPException:
        raise
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"TTS failed: {err}") from err
