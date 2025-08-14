import asyncio
import time
from typing import Dict, Any, List

class SpeakerState:
    def __init__(self, client_id: str, display_name: str):
        self.client_id = client_id
        self.display_name = display_name
        self.last_dbfs = float("-inf")
        self.last_text = ""
        self.last_update = time.monotonic()
        self.connected = True

class StreamManager:
    """
    Manager that stores speaker states, teacher websocket clients, and history.
    API used by app.py:
      - add_speaker(client_id, display_name)
      - remove_speaker(client_id)
      - update_intensity(client_id, dbfs)
      - set_transcript(client_id, text)
      - rank_speakers() -> list of SpeakerState (sorted)
      - broadcast_ranking() -> sends JSON {"type":"ranking","data": [...] } to teacher clients
      - get_history(limit)
      - clear_history()
    """
    def __init__(self):
        self.speakers: Dict[str, SpeakerState] = {}
        self.teacher_clients: List[Any] = []
        self.lock = asyncio.Lock()
        self.history: List[dict] = []

    async def add_speaker(self, client_id: str, display_name: str):
        async with self.lock:
            self.speakers[client_id] = SpeakerState(client_id, display_name)

    async def remove_speaker(self, client_id: str):
        async with self.lock:
            if client_id in self.speakers:
                del self.speakers[client_id]

    async def update_intensity(self, client_id: str, dbfs: float):
        async with self.lock:
            if client_id in self.speakers:
                s = self.speakers[client_id]
                s.last_dbfs = dbfs
                s.last_update = time.monotonic()

    async def set_transcript(self, client_id: str, text: str):
        async with self.lock:
            if client_id in self.speakers:
                s = self.speakers[client_id]
                s.last_text = text
                s.last_update = time.monotonic()
                # add to history (protected)
                await self._add_history_unlocked(s.display_name, text)

    async def _add_history_unlocked(self, name: str, text: str):
        ts = time.strftime("%H:%M:%S")
        self.history.append({"time": ts, "name": name, "text": text})
        # cap history size
        if len(self.history) > 2000:
            self.history = self.history[-2000:]

    async def get_history(self, limit: int = 200) -> List[dict]:
        async with self.lock:
            return list(self.history[-limit:])

    async def clear_history(self):
        async with self.lock:
            self.history = []

    async def rank_speakers(self) -> List[SpeakerState]:
        async with self.lock:
            # return SpeakerState objects sorted by last_dbfs desc
            return sorted(self.speakers.values(), key=lambda s: s.last_dbfs, reverse=True)

    async def broadcast_ranking(self):
        ranking = await self.rank_speakers()
        payload = [
            {
                "clientId": s.client_id,
                "name": s.display_name,
                "dbfs": round(s.last_dbfs, 1) if s.last_dbfs != float("-inf") else -120.0,
                "text": s.last_text,
            }
            for s in ranking
        ]
        dead = []
        # send to teacher clients (remove dead ones)
        for ws in list(self.teacher_clients):
            try:
                await ws.send_json({"type": "ranking", "data": payload})
            except Exception:
                dead.append(ws)
        for ws in dead:
            try:
                self.teacher_clients.remove(ws)
            except ValueError:
                pass
