"""Small, dependency-light helpers for editor audio previews.

The pygame mixer exposes volume as a 0..1 channel gain.  The editor needs a
little more headroom for quiet source files, so gains above 1 are applied to a
decoded PCM buffer first and peak-limited before the buffer is sent back to
pygame.  This module is intentionally independent of Qt so it can also be
covered by the audio service tests.
"""

from __future__ import annotations

import os
import wave

import pygame


def ensure_mixer():
    """Return the mixer format, initializing pygame's mixer when needed."""
    init = pygame.mixer.get_init()
    if init:
        return init
    pygame.mixer.init()
    return pygame.mixer.get_init()


def get_audio_duration(path: str) -> float | None:
    """Return a decoded file's duration in seconds, or ``None`` on failure."""
    if not path or not os.path.isfile(path):
        return None
    try:
        if os.path.splitext(path)[1].lower() == ".wav":
            with wave.open(path, "rb") as source:
                rate = source.getframerate()
                if rate:
                    return max(0.0, source.getnframes() / float(rate))
        ensure_mixer()
        return max(0.0, float(pygame.mixer.Sound(path).get_length()))
    except (OSError, wave.Error, pygame.error, TypeError, ValueError):
        return None


def trim_sound(sound, start: float = 0.0, end: float | None = None):
    """Return a mixer-compatible PCM slice of ``sound``."""
    try:
        start = max(0.0, float(start or 0.0))
        end = None if end in (None, "") else max(0.0, float(end))
    except (TypeError, ValueError):
        return None

    length = max(0.0, float(sound.get_length()))
    end = length if end is None else min(end, length)
    if start >= end:
        return None
    if start <= 0.0 and end >= length:
        return sound

    init = ensure_mixer()
    if not init or not hasattr(sound, "get_raw"):
        return None
    sample_rate, sample_format, channels = init
    bytes_per_sample = max(1, abs(int(sample_format)) // 8)
    frame_bytes = bytes_per_sample * int(channels)
    raw = sound.get_raw()
    first = int(round(start * sample_rate)) * frame_bytes
    last = int(round(end * sample_rate)) * frame_bytes
    raw_slice = raw[first:last]
    return pygame.mixer.Sound(buffer=raw_slice) if raw_slice else None


def peak_limited_gain_sound(sound, gain: float):
    """Apply gain to a sound without allowing PCM samples to clip.

    Gains at or below 1 are left to the mixer channel.  For larger gains, the
    source is scaled to a 0.98 peak ceiling.  A quiet file can therefore be
    amplified while a hot file is automatically limited rather than hard
    clipped.
    """
    try:
        gain = max(0.0, min(2.0, float(gain)))
    except (TypeError, ValueError):
        return sound
    if gain <= 1.0 or not hasattr(sound, "get_raw"):
        return sound

    try:
        import numpy as np

        init = ensure_mixer()
        sample_format = int(init[1])
        bits = abs(sample_format)
        if bits not in (8, 16, 32):
            return sound
        signed = sample_format < 0
        if bits == 8:
            dtype = np.int8 if signed else np.uint8
            center = 0.0 if signed else 128.0
            peak_value = 127.0
        elif bits == 16:
            dtype = np.int16 if signed else np.uint16
            center = 0.0 if signed else 32768.0
            peak_value = 32767.0
        else:
            dtype = np.int32 if signed else np.uint32
            center = 0.0 if signed else 2147483648.0
            peak_value = 2147483647.0

        samples = np.frombuffer(sound.get_raw(), dtype=dtype).astype(np.float64)
        if not samples.size:
            return sound
        samples -= center
        peak = float(np.max(np.abs(samples)))
        if peak <= 0.0:
            return sound
        applied_gain = min(gain, (peak_value * 0.98) / peak)
        samples *= applied_gain
        samples = np.clip(samples, -peak_value * 0.98, peak_value * 0.98)
        samples += center
        return pygame.mixer.Sound(buffer=np.rint(samples).astype(dtype).tobytes())
    except (ImportError, OSError, pygame.error, TypeError, ValueError):
        return sound
