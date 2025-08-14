import numpy as np

# Try to use faster-whisper locally; otherwise fallback to placeholder text.
try:
    from faster_whisper import WhisperModel
    _model = WhisperModel("small", compute_type="int8")
except Exception as e:
    _model = None
    _model_err = e

def transcribe_pcm16(pcm16: bytes, sample_rate: int = 16000) -> str:
    """
    Transcribe 16-bit PCM mono audio. If faster-whisper isn't available,
    returns a placeholder string.
    """
    if _model is None:
        return "[ASR disabled or model missing]"
    arr = np.frombuffer(pcm16, dtype=np.int16).astype("float32") / 32768.0
    segments, info = _model.transcribe(arr, language="en", beam_size=1)
    text = "".join(seg.text for seg in segments).strip()
    return text
