// client.js - capture mic, downsample to 16k, send float32 PCM via WebSocket
let ws = null;
let audioCtx, processor, source, stream;

async function start() {
  const name = document.getElementById("name").value || "Student";
  const scheme = location.protocol === "https:" ? "wss" : "ws";
  const url = `${scheme}://${window.location.host}/ws/student?name=${encodeURIComponent(name)}`;
  ws = new WebSocket(url);
  ws.binaryType = "arraybuffer";
  document.getElementById("status").textContent = "connecting...";

  ws.onopen = () => { document.getElementById("status").textContent = "connected"; };
  ws.onclose = () => { document.getElementById("status").textContent = "closed"; stopAudio(); };
  ws.onerror = () => { document.getElementById("status").textContent = "error"; };

  stream = await navigator.mediaDevices.getUserMedia({audio: {echoCancellation: true, noiseSuppression: true, autoGainControl: false}});
  audioCtx = new (window.AudioContext || window.webkitAudioContext)({sampleRate: 48000});
  source = audioCtx.createMediaStreamSource(stream);

  const desiredSamplesPerCallback = 1024;
  processor = audioCtx.createScriptProcessor(desiredSamplesPerCallback, 1, 1);
  source.connect(processor);
  processor.connect(audioCtx.destination);

  const downsampleRatio = audioCtx.sampleRate / 16000;
  let leftover = new Float32Array(0);

  processor.onaudioprocess = (e) => {
    const input = e.inputBuffer.getChannelData(0);
    const concat = new Float32Array(leftover.length + input.length);
    concat.set(leftover, 0);
    concat.set(input, leftover.length);

    const outLen = Math.floor(concat.length / downsampleRatio);
    const out = new Float32Array(outLen);
    for (let i = 0; i < outLen; i++) {
      const idx = Math.floor(i * downsampleRatio);
      out[i] = concat[idx];
    }

    const consumed = outLen * downsampleRatio;
    const remain = concat.length - Math.floor(consumed);
    leftover = new Float32Array(remain);
    leftover.set(concat.subarray(concat.length - remain));

    // level meter UI
    let rms = 0;
    for (let i = 0; i < out.length; i++) rms += out[i]*out[i];
    rms = Math.sqrt(rms / Math.max(1, out.length));
    const pct = Math.min(100, Math.max(0, Math.round(rms * 200)));
    document.getElementById("level").style.width = pct + "%";

    if (ws && ws.readyState === WebSocket.OPEN && out.length > 0) {
      ws.send(out.buffer);
    }
  };
}

function stopAudio() {
  try { if (processor) processor.disconnect(); } catch{}
  try { if (source) source.disconnect(); } catch{}
  try { if (audioCtx) audioCtx.close(); } catch{}
  try { if (stream) stream.getTracks().forEach(t => t.stop()); } catch{}
}

window.addEventListener("load", () => {
  document.getElementById("connect").addEventListener("click", start);
});
