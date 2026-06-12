"""
Hume AI vocal prosody analysis.

Streams session audio to Hume's Expression Measurement streaming API
(prosody model) and aggregates the 48-emotion scores into interview
metrics: confidence, nervousness, and energy. Trained ML scores —
not rule-based heuristics.

Degrades gracefully: returns None when HUME_API_KEY is unset or the
API is unreachable, so the interview flow never depends on Hume.
"""

import asyncio
import base64
import io
import json
import logging
import os
import wave

import numpy as np
import websockets

logger = logging.getLogger(__name__)

HUME_STREAM_URL = "wss://api.hume.ai/v0/stream/models"

# Hume streaming accepts at most ~5 seconds of audio per message.
CHUNK_SECONDS = 5.0
# Bound API usage: analyze at most this many chunks per session (5 min of audio).
MAX_CHUNKS = 60

# Mapping from Hume's prosody emotion labels onto interview metrics.
CONFIDENCE_EMOTIONS = {"Determination", "Pride", "Interest", "Calmness", "Concentration"}
NERVOUSNESS_EMOTIONS = {"Anxiety", "Distress", "Doubt", "Awkwardness", "Fear", "Embarrassment"}
ENERGY_EMOTIONS = {"Excitement", "Joy", "Amusement", "Enthusiasm", "Triumph"}


def _float32_chunk_to_wav_b64(chunk: np.ndarray, sample_rate: int) -> str:
    pcm16 = np.clip(chunk, -1.0, 1.0)
    pcm16 = (pcm16 * 32767.0).astype(np.int16)

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm16.tobytes())

    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _extract_emotion_scores(message: dict) -> dict[str, float]:
    """Pull {emotion_name: score} out of a Hume prosody stream response."""
    scores: dict[str, float] = {}
    predictions = (message.get("prosody") or {}).get("predictions") or []
    for prediction in predictions:
        for emotion in prediction.get("emotions") or []:
            name = emotion.get("name")
            score = emotion.get("score")
            if not name or not isinstance(score, (int, float)):
                continue
            # Average across multiple speech segments in the same chunk
            if name in scores:
                scores[name] = (scores[name] + float(score)) / 2.0
            else:
                scores[name] = float(score)
    return scores


def _mean_of(scores: dict[str, float], names: set[str]) -> float:
    values = [scores[n] for n in names if n in scores]
    if not values:
        return 0.0
    return sum(values) / len(values)


async def analyze_prosody(audio: np.ndarray, sample_rate: int = 16000) -> dict | None:
    """
    Run Hume prosody analysis over a full session's audio.

    Args:
        audio: Mono float32 samples in [-1, 1].
        sample_rate: Samples per second (16000 from the voice pipeline).

    Returns:
        Aggregated prosody metrics dict, or None when unavailable.
    """
    api_key = os.getenv("HUME_API_KEY")
    if not api_key:
        logger.info("HUME_API_KEY not set; skipping prosody analysis")
        return None

    if audio.size < sample_rate:  # less than 1 second of speech
        logger.info("Not enough audio for prosody analysis")
        return None

    chunk_samples = int(CHUNK_SECONDS * sample_rate)
    chunks = [
        audio[i : i + chunk_samples]
        for i in range(0, len(audio), chunk_samples)
    ][:MAX_CHUNKS]

    per_chunk_scores: list[dict[str, float]] = []

    try:
        async with websockets.connect(
            HUME_STREAM_URL,
            additional_headers={"X-Hume-Api-Key": api_key},
            max_size=2**24,
        ) as ws:
            for chunk in chunks:
                if chunk.size < sample_rate // 2:
                    continue
                payload = {
                    "models": {"prosody": {}},
                    "data": _float32_chunk_to_wav_b64(chunk, sample_rate),
                }
                await ws.send(json.dumps(payload))
                raw = await asyncio.wait_for(ws.recv(), timeout=15)
                message = json.loads(raw)
                if message.get("error"):
                    logger.warning("Hume returned an error: %s", message["error"])
                    continue
                scores = _extract_emotion_scores(message)
                if scores:
                    per_chunk_scores.append(scores)
    except Exception:
        logger.exception("Hume prosody streaming failed")
        if not per_chunk_scores:
            return None

    if not per_chunk_scores:
        logger.info("Hume returned no usable prosody predictions")
        return None

    # Aggregate emotion scores across all chunks
    aggregate: dict[str, float] = {}
    for scores in per_chunk_scores:
        for name, score in scores.items():
            aggregate.setdefault(name, 0.0)
            aggregate[name] += score
    for name in aggregate:
        aggregate[name] /= len(per_chunk_scores)

    top_emotions = sorted(aggregate.items(), key=lambda kv: kv[1], reverse=True)[:8]

    confidence = _mean_of(aggregate, CONFIDENCE_EMOTIONS)
    nervousness = _mean_of(aggregate, NERVOUSNESS_EMOTIONS)
    energy = _mean_of(aggregate, ENERGY_EMOTIONS)

    result = {
        "source": "hume",
        "chunks_analyzed": len(per_chunk_scores),
        "confidence": round(min(1.0, confidence * 2.0), 4),
        "nervousness": round(min(1.0, nervousness * 2.0), 4),
        "energy": round(min(1.0, energy * 2.0), 4),
        "top_emotions": [{"name": name, "score": round(score, 4)} for name, score in top_emotions],
    }
    logger.info(
        "Hume prosody analysis complete",
        extra={"chunks": len(per_chunk_scores), "confidence": result["confidence"], "nervousness": result["nervousness"]},
    )
    return result


FILLER_WORDS = {"um", "uh", "mhmm", "mm-mm", "uh-uh", "uh-huh", "nuh-uh", "like", "hmm"}


def compute_speech_metrics(session_words: list[dict]) -> dict | None:
    """Compute pace (WPM) and filler-word stats from Deepgram word timestamps."""
    words = [w for w in session_words if w.get("word")]
    if len(words) < 5:
        return None

    first_start = float(words[0].get("start") or 0.0)
    last_end = float(words[-1].get("end") or 0.0)
    duration_s = max(1.0, last_end - first_start)

    total = len(words)
    fillers = sum(1 for w in words if str(w["word"]).strip(".,!?").lower() in FILLER_WORDS)

    pace_wpm = total / duration_s * 60.0
    filler_ratio = fillers / total
    # 120-160 WPM is the comfortable interview band
    if 120 <= pace_wpm <= 160:
        pace_score = 1.0
    else:
        deviation = min(abs(pace_wpm - 120), abs(pace_wpm - 160))
        pace_score = max(0.0, 1.0 - (deviation / 10.0) * 0.05)

    clarity_score = max(0.0, 1.0 - filler_ratio * 10.0)

    return {
        "pace_wpm": round(pace_wpm, 1),
        "pace_score": round(pace_score, 4),
        "filler_count": fillers,
        "total_words": total,
        "filler_ratio": round(filler_ratio, 4),
        "clarity_score": round(clarity_score, 4),
        "speech_duration_seconds": round(duration_s, 1),
    }
