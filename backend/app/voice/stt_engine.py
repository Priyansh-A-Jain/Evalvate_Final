import asyncio
import json
import logging
import os
from typing import Callable

import websockets

logger = logging.getLogger(__name__)


class DeepgramEngine:
    def __init__(self, on_word: Callable[[dict], None]):
        self.url = (
            "wss://api.deepgram.com/v1/listen"
            "?model=nova-2"
            "&encoding=linear16"
            "&sample_rate=16000"
            "&channels=1"
            "&smart_format=true"
            "&interim_results=true"
            "&endpointing=300"
            "&filler_words=true"
        )
        self.api_key = (os.getenv("DEEPGRAM_API_KEY") or "").strip()
        self.ws = None
        self.on_word = on_word
        self.receive_task = None
        self.last_error: str | None = None

    async def connect(self) -> bool:
        self.last_error = None
        if not self.api_key:
            self.last_error = "DEEPGRAM_API_KEY is not set in backend/.env"
            logger.error(self.last_error)
            return False

        headers = {"Authorization": f"Token {self.api_key}"}
        try:
            self.ws = await asyncio.wait_for(
                websockets.connect(self.url, additional_headers=headers, ping_interval=20, ping_timeout=20),
                timeout=15,
            )
            logger.info("Connected to Deepgram streaming STT")
            self.receive_task = asyncio.create_task(self._listen())
            return True
        except Exception as exc:
            self.last_error = str(exc)
            logger.error("Failed to connect to Deepgram STT: %s", exc)
            self.ws = None
            return False

    async def send_audio(self, pcm_bytes: bytes):
        if not self.ws:
            return
        try:
            await self.ws.send(pcm_bytes)
        except websockets.exceptions.ConnectionClosed:
            self.ws = None

    async def close(self):
        try:
            if self.ws:
                await self.ws.send(b"")
                await asyncio.sleep(0.3)
                await self.ws.close()
        except Exception:
            pass

        if self.receive_task:
            self.receive_task.cancel()
            self.receive_task = None
        self.ws = None

    async def _listen(self):
        try:
            async for message in self.ws:
                data = json.loads(message)
                if "channel" not in data:
                    continue

                is_final = data.get("is_final", False)
                alternatives = data["channel"].get("alternatives", [])
                if not alternatives:
                    continue

                transcript = (alternatives[0].get("transcript") or "").strip()
                words = alternatives[0].get("words", [])

                if is_final:
                    for w in words:
                        self.on_word(
                            {
                                "word": w.get("word"),
                                "start": w.get("start"),
                                "end": w.get("end"),
                                "interim": False,
                            }
                        )
                elif transcript:
                    self.on_word(
                        {
                            "word": transcript,
                            "start": words[0].get("start", 0) if words else 0,
                            "end": words[-1].get("end", 0) if words else 0,
                            "interim": True,
                        }
                    )
        except asyncio.CancelledError:
            pass
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Deepgram STT connection closed")
        except Exception as exc:
            logger.error("Deepgram listen error: %s", exc)
