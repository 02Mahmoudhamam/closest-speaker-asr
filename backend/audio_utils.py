import math
import time
import numpy as np
import webrtcvad

FRAME_MS = 20  # webrtcvad supports 10/20/30
SAMPLE_RATE = 16000
SAMPLES_PER_FRAME = SAMPLE_RATE * FRAME_MS // 1000
BYTES_PER_SAMPLE = 2  # int16

def float_to_int16(pcm: np.ndarray) -> np.ndarray:
    """Convert float32 PCM [-1,1] to int16 PCM"""
    pcm = np.clip(pcm, -1.0, 1.0)
    return (pcm * 32767.0).astype(np.int16)

def pcm16_rms(int16_arr: np.ndarray) -> float:
    if int16_arr.size == 0:
        return 0.0
    return float(math.sqrt(np.mean((int16_arr.astype(np.float64)) ** 2)))

def rms_to_dbfs(rms: float) -> float:
    if rms <= 0:
        return float("-inf")
    return 20.0 * math.log10(rms / 32768.0)

def apply_noise_gate_int16(int16_arr: np.ndarray, threshold_dbfs: float = -60.0) -> np.ndarray:
    """
    Simple noise gate for intensity measurement: frames below threshold are zeroed.
    Used only for ranking (does not change audio used for VAD/ASR).
    """
    if int16_arr.size == 0:
        return int16_arr
    rms = pcm16_rms(int16_arr)
    db = rms_to_dbfs(rms)
    if not np.isfinite(db):
        return int16_arr
    if db < threshold_dbfs:
        return np.zeros_like(int16_arr)
    return int16_arr

class VadStream:
    """
    Buffering + VAD for a single stream. Returns utterance bytes when speech segment ends.
    """
    def __init__(self, aggressiveness: int = 2, silence_ms: int = 400):
        self.vad = webrtcvad.Vad(aggressiveness)
        self.buffer = bytearray()
        self.frame_bytes = SAMPLES_PER_FRAME * BYTES_PER_SAMPLE
        self.active = False
        self.silence_ms = silence_ms
        self.silence_frames_needed = max(1, silence_ms // FRAME_MS)
        self.silence_frames = 0
        self.current_utterance = bytearray()
        self.last_intensity_dbfs = float("-inf")
        self.last_active_ts = 0.0

    def push_pcm16(self, chunk: bytes, now_ts: float):
        """Append raw int16 PCM @16k; update VAD and intensity; return utterance bytes if ended."""
        utterance = None
        self.buffer.extend(chunk)
        while len(self.buffer) >= self.frame_bytes:
            frame = bytes(self.buffer[:self.frame_bytes])
            del self.buffer[:self.frame_bytes]

            is_speech = self.vad.is_speech(frame, SAMPLE_RATE)

            # intensity
            int16 = np.frombuffer(frame, dtype=np.int16)
            rms = pcm16_rms(int16)
            self.last_intensity_dbfs = rms_to_dbfs(rms)

            if is_speech:
                self.active = True
                self.silence_frames = 0
                self.current_utterance.extend(frame)
                self.last_active_ts = now_ts
            else:
                if self.active:
                    self.silence_frames += 1
                    self.current_utterance.extend(frame)
                    if self.silence_frames >= self.silence_frames_needed:
                        utterance = bytes(self.current_utterance)
                        self.current_utterance = bytearray()
                        self.active = False
                        self.silence_frames = 0
        return utterance
