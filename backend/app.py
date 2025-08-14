import os
import time
import numpy as np
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from audio_utils import float_to_int16, VadStream, apply_noise_gate_int16, pcm16_rms, rms_to_dbfs
from manager import StreamManager
from asr import transcribe_pcm16

# compute frontend folder relative to backend file location (robust)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app = FastAPI(title="Closest Speaker & Ranked ASR (Stable)")

# Mount frontend only if directory exists; otherwise provide helpful message
if os.path.isdir(FRONTEND_DIR):
    app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")
else:
    @app.get("/frontend/{path:path}")
    async def frontend_missing(path: str):
        return HTMLResponse(
            f"<h3>Frontend not found</h3>"
            f"<p>Expected frontend directory at: <code>{FRONTEND_DIR}</code></p>"
            f"<p>Please ensure your project structure is:</p>"
            f"<pre>project-root/\\n  backend/\\n    app.py\\n  frontend/\\n    index.html\\n    teacher.html</pre>",
            status_code=404
        )

manager = StreamManager()

@app.get("/")
async def root():
    return {"ok": True, "msg": "Open /frontend/index.html and /frontend/teacher.html"}

@app.get("/history")
async def get_history(limit: int = 200):
    return await manager.get_history(limit)

@app.post("/history/clear")
async def clear_history():
    await manager.clear_history()
    return {"ok": True, "msg": "History cleared"}

@app.websocket("/ws/student")
async def ws_student(ws: WebSocket, name: Optional[str] = Query(default="Student")):
    await ws.accept()
    client_id = f"{id(ws)}"
    await manager.add_speaker(client_id, name)
    vad_stream = VadStream(aggressiveness=2, silence_ms=400)
    try:
        while True:
            # Expect binary Float32 PCM @16k frames from client
            data = await ws.receive_bytes()
            now = time.monotonic()
            if len(data) % 4 != 0:
                continue
            f32 = np.frombuffer(data, dtype=np.float32)
            int16 = float_to_int16(f32)

            # keep VAD logic unchanged (assemble utterances)
            utterance = vad_stream.push_pcm16(int16.tobytes(), now_ts=now)

            # compute gated intensity (for ranking) - non-destructive
            try:
                gated = apply_noise_gate_int16(int16, threshold_dbfs=-60.0)
                gated_rms = pcm16_rms(gated)
                gated_dbfs = rms_to_dbfs(gated_rms)
                effective_dbfs = gated_dbfs if gated_dbfs != float("-inf") else vad_stream.last_intensity_dbfs
            except Exception:
                effective_dbfs = vad_stream.last_intensity_dbfs

            await manager.update_intensity(client_id, effective_dbfs)
            await manager.broadcast_ranking()

            # when utterance ended -> transcribe only if this stream is currently closest
            ranking = await manager.rank_speakers()
            if ranking and ranking[0].client_id == client_id and utterance:
                try:
                    text = transcribe_pcm16(utterance, sample_rate=16000)
                except Exception as e:
                    text = f"[asr-error] {e}"
                await manager.set_transcript(client_id, text)
                await manager.broadcast_ranking()

    except WebSocketDisconnect:
        await manager.remove_speaker(client_id)
        await manager.broadcast_ranking()
    except Exception:
        await manager.remove_speaker(client_id)
        await manager.broadcast_ranking()

@app.websocket("/ws/teacher")
async def ws_teacher(ws: WebSocket):
    await ws.accept()
    manager.teacher_clients.append(ws)
    await manager.broadcast_ranking()
    try:
        while True:
            await ws.receive_text()  # keepalive / ignore
    except WebSocketDisconnect:
        try:
            manager.teacher_clients.remove(ws)
        except ValueError:
            pass
