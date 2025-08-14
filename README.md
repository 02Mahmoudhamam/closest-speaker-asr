
# Closest Speaker & Ranked ASR System (Premium Version)

## 🚀 Project Idea

This project aims to create a **real-time intelligent system to detect the closest speaker among multiple students**, convert their speech to text (ASR), and display it ordered from closest to farthest.  
Ideal for **classrooms, group meetings, or any multi-speaker environment** where focusing on the nearest speaker is important.

---

## 🛠 Core Features

### 1️⃣ Audio Capture
- Uses **WebSocket** to stream audio from each student to the backend.
- Supports **16kHz Float32 PCM** audio.
- Each student connects with a unique name.

### 2️⃣ Voice Activity Detection (VAD)
- Uses **VadStream** to detect when a student is speaking.
- Collects full utterances before sending them to ASR.

### 3️⃣ Sound Intensity Measurement
- Converts PCM from float32 to int16.
- Calculates **RMS and dBFS** for each speaker.
- Ranks speakers by intensity → closest speaker first.

### 4️⃣ Speech-to-Text (ASR)
- Sends audio of **only the closest speaker** to the ASR engine:
  - Supported engines: OpenAI Whisper, Google Speech-to-Text, Azure Speech.
- Displays the transcribed text in real-time for teacher and students.

### 5️⃣ Frontend Interface
- **Student page (`index.html`)**:
  - Button to start microphone and stream audio.
  - Sends student name with each connection.
- **Teacher page (`teacher.html`)**:
  - Displays ranked list of speakers from closest to farthest.
  - Shows live transcribed text.
- Built with HTML/CSS/JavaScript for simplicity.

### 6️⃣ History Management
- Retrieve the **History** of transcribed phrases (up to 200 by default).
- Clear history via `/history/clear` endpoint.
- Can be extended with an interactive frontend for live updates.

---

## ⚙️ Running the Project

### 1️⃣ Requirements
- Python 3.11+
## 2️⃣ Start the Server
# Activate virtual environment
.venv\Scripts\activate

# Run the server
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000

## 3️⃣ Access the Frontend

Student: http://127.0.0.1:8000/frontend/index.html

Teacher: http://127.0.0.1:8000/frontend/teacher.html

## 4️⃣ Quick Tests

Test root endpoint:

Invoke-WebRequest -Uri http://127.0.0.1:8000/ -UseBasicParsing | Select-Object -Expand Content


Check history endpoint:

Invoke-WebRequest -Uri http://127.0.0.1:8000/history -UseBasicParsing | Select-Object -Expand Content


## 💡 Future Enhancements

Interactive History UI

Display last 200 transcribed phrases.

Live updates when new text arrives.

Clear history button without page reload.

Advanced Noise Filtering

Automatically remove distant or background noise.

Classroom Map

Show speaker positions based on intensity.

Text-to-Speech Feedback

Read transcribed text aloud to teacher or students.

Multi-ASR Engine Support

Option to switch between Whisper, Google, or Azure ASR engines.

## 📝 Notes

Core functionality has been tested on Python 3.11 with a virtual environment.

Designed to run safely without breaking frontend or WebSocket functionality, even if a student or teacher connection fails.

Additional features can be added without affecting the main logic.

## 📧 Contact / Support

For questions, extensions, or technical support:
Mahmoudhamam892@gmail.com



- Install dependencies:
```bash
pip install -r requirements.txt
Required packages: webrtcvad or pyannote.audio for VAD.

ASR engine (Whisper, Google, or Azure).
##📂 Project Structure
project-root/
│
├─ backend/
│   ├─ app.py               # Main server
│   ├─ manager.py           # Manages speakers and ranking
│   ├─ audio_utils.py       # VAD, audio conversion, RMS, noise gate
│   ├─ asr.py               # ASR interface
│   └─ .venv/               # Virtual environment
│
├─ frontend/
│   ├─ index.html           # Student interface
│   ├─ teacher.html         # Teacher interface
│   └─ client.js            # WebSocket audio streaming
│
└─ README.md
