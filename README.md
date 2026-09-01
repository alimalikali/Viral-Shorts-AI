# ⚡ Viral Shorts AI

Viral Shorts AI is a self-hosted, 100% open-source desktop and web platform that automates the analysis of long-form videos to generate short-form, high-engagement clips optimized for **TikTok, YouTube Shorts, and Reels**. 

It uses open-source local AI models, meaning **no paid APIs, no monthly subscriptions, and complete offline privacy**.

---

## ✨ Features

- **AI Viral Moment Detection**: OpenCV scene histogram analytics + speech intensity peaks + transcription hook filters.
- **AI Smart Reframer**: Converts landscape `16:9` footage into mobile portrait `9:16` using face/object detection with a rolling-average panning filter (simulates professional panning).
- **TikTok-style Captions**: Generates styled word-by-word highlighted ASS overlays featuring emojis, impact typography, and thick borders.
- **Built-in Video Editor**: Cuts, crops, trims, and implements speed dials.
- **Auto Silence Remover**: Isolates active talking boundaries and cuts out speech silence gaps.
- **Future-Proof Plugin Architecture**: Dynamic import module allowing you to drop new models (e.g., custom transformers or audio filters) directly into `/plugins/`.

---

## 🏗️ Directory Layout

```
├── backend/                  # Python FastAPI API & AI Processing queue
│   ├── app/
│   │   ├── ai/               # Whisper, OpenCV & FFmpeg engines
│   │   └── plugins/          # Dynamic plugin systems
│   └── Dockerfile
├── frontend/                 # React, Vite, TS, Tailwind UI client
│   ├── src/
│   │   └── components/       # Timeline, Canvas Player, Upload widgets
│   └── Dockerfile
├── desktop/                  # Electron native wrapper container
├── docker-compose.yml        # Multi-container orchestration
└── setup_and_run.bat         # Single-click Windows bootstrapper
```

---

## 🚀 One-Click Windows Setup

If you are on Windows, we have bundled all commands into a single setup file:
1. Double-click `setup_and_run.bat`.
2. The script will automatically configure your Python `venv`, install Python requirements, pull frontend NPM assets, and launch:
   - **Backend API Server** (`http://localhost:8000`)
   - **React Web Workspace** (`http://localhost:3000`)
   - **Native Electron Desktop UI** (opens immediately as a desktop app!)

---

## 🐳 Docker Deployment (Web Dashboard)

For hosting on servers, home labs, or local containers:
```bash
docker-compose up --build
```
Once built, open `http://localhost:3000` to access the editor workspace.

---

## 🐧 One-Command Linux Setup

```bash
./run.sh
```

Starts the backend on `:8000`, the Vite client on `:3000`, and the Electron window, and shuts
the background services down when you close Electron. Requires `ffmpeg`, `node`, and
`python3.12` on PATH. Override ports with `BACKEND_PORT` / `FRONTEND_PORT`.

---

## 🛠️ Step-by-Step Manual Setup

### 1. Start Python Backend
```bash
cd backend
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --port 8000 --reload
```

### 2. Start Vite Web Client
```bash
cd frontend
npm install
npm run dev
```

### 3. Open Electron Desktop Client
```bash
cd desktop
npm install
npm start
```

---

## 📤 How to Push to your GitHub Account

To upload this complete software to your own GitHub account and get a shareable repository link:

1. **Create Repository**: Go to [GitHub](https://github.com) and create a new **public or private** repository named `viral-shorts-ai` (leave "Initialize with README/gitignore" **unchecked**).
2. **Open Terminal**: Open Command Prompt/PowerShell in this directory:
   ```cmd
   d:
   cd "d:\pro\SOFTWARE CLIPPER"
   ```
3. **Commit & Push**: Run the following git commands:
   ```bash
   # Initialize repository
   git init
   
   # Stage and commit all files
   git add .
   git commit -m "Initial commit: Complete open-source Viral Shorts AI stack"
   
   # Set branch name to main
   git branch -M main
   
   # Link to your new GitHub repository (REPLACE with your actual username)
   git remote add origin https://github.com/YOUR_GITHUB_USERNAME/viral-shorts-ai.git
   
   # Push files
   git push -u origin main
   ```
---

## 📄 License
This project is licensed under the MIT License - open-source, self-hosted, and free forever.
