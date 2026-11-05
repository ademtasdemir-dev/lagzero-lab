"""Whisper transcription of the mic track, restricted to regions with voice."""

from __future__ import annotations

import re

import numpy as np

# Phrases Whisper tends to invent on noise (mostly from subtitle training data).
HALLUCINATIONS = re.compile(
    r"untertitel|amara\.org|zdf|copyright|www\.|\.de\b|subtitles by|"
    r"vertraue und glaube|göttliche kraft|"
    # alone it is the classic subtitle ending; inside a real goodbye it is kept (episode end!)
    r"^\W*vielen dank fürs zuschauen\W*$|"
    # outro phrases Whisper writes on gunfire and explosions when they stand alone
    r"^\W*(bis zum nächsten mal|das war'?s für heute|tschüss|danke fürs zuschauen|vielen dank)\W*$",
    re.IGNORECASE,
)
# Whisper's way of "transcribing" music: a lone tag, or one sound repeated over and over.
MUSIC = re.compile(r"^\W*(musik|music|applaus|♪+)\W*$|\b(\w{1,5})\b(?:\W+\2\b){5,}"
                   # a group of up to four words in a loop ("du bist der nacht du bist der nacht ...")
                   r"|\b(\w+(?:\W+\w+){0,3})\b(?:\W+\3\b){3,}", re.IGNORECASE)


def is_noise(text: str) -> bool:
    return bool(HALLUCINATIONS.search(text) or MUSIC.search(text))


def load_asr(cfg: dict):
    import torch
    from transformers import pipeline

    device = int(cfg.get("device") or 0) if torch.cuda.is_available() else -1  # GPU index (second card in 2-GPU mode)
    dtype = torch.float16 if device >= 0 else torch.float32
    return pipeline("automatic-speech-recognition", model=cfg["model"], torch_dtype=dtype, device=device)


def free_vram() -> None:
    """Call after dropping the last reference to the ASR pipeline."""
    import torch

    if torch.cuda.is_available():
        torch.cuda.empty_cache()  # free VRAM for the next step


def transcribe_regions(pcm: np.ndarray, sample_rate: int, regions: list[tuple[float, float]], cfg: dict,
                       progress=None) -> list[dict]:
    asr = load_asr(cfg)

    segments: list[dict] = []
    batch = int(cfg["batch_size"])
    for i in range(0, len(regions), batch):
        group = regions[i:i + batch]
        inputs = [
            {"raw": np.asarray(pcm[int(s * sample_rate):int(e * sample_rate)], dtype=np.float32) / 32768.0,
             "sampling_rate": sample_rate}
            for s, e in group
        ]
        results = asr(inputs, batch_size=batch, return_timestamps=True,
                      generate_kwargs={"language": cfg["language"], "task": "transcribe"})
        for (start, end), res in zip(group, results):
            for chunk in res.get("chunks") or [{"timestamp": (0.0, end - start), "text": res["text"]}]:
                text = chunk["text"].strip()
                if not text or is_noise(text):
                    continue
                a, b = chunk["timestamp"]
                a = start + (a or 0.0)
                b = start + (b if b is not None else end - start)
                b = max(min(b, end), a)  # Whisper sometimes returns an end before the start
                segments.append({"start": round(a, 2), "end": round(b, 2), "text": text})
        if progress:
            progress(min(i + batch, len(regions)), len(regions))

    del asr
    free_vram()
    return drop_repeats(segments)


def drop_repeats(segments: list[dict], keep: int = 2, window_s: float = 30.0) -> list[dict]:
    """Whisper on noisy audio repeats one sentence second after second ("Was ist das?" x30).

    The same text more than `keep` times within `window_s` seconds is invented: only the first ones stay.
    """
    def norm(text: str) -> str:
        return re.sub(r"\W+", " ", text.lower()).strip()

    out, seen = [], {}
    for seg in sorted(segments, key=lambda s: s["start"]):
        key = norm(seg["text"])
        times = [t for t in seen.get(key, []) if seg["start"] - t <= window_s]
        seen[key] = times + [seg["start"]]
        if len(times) < keep:
            out.append(seg)
    return out
