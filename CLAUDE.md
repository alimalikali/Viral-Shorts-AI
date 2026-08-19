# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Viral Shorts AI — self-hosted, fully-local pipeline that ingests long-form video and emits 9:16 short-form clips with burned-in TikTok-style captions. No paid APIs; runs against local Whisper / OpenCV / FFmpeg.

## Repo layout (three deployables, one shared API)

- `backend/` — FastAPI app (`app.main:app`) + an in-process `asyncio.Queue` worker. This is the only thing that does real work.
- `frontend/` — React 18 + Vite + TS + Tailwind SPA. Calls the backend with relative `/api/...` paths.
- `desktop/` — Electron shell that `loadURL`s the Vite server (`FRONTEND_PORT`, default 3000). Has no logic of its own.
- `docker-compose.yml` — builds `backend` (port 8000) and `frontend` (Nginx on port 3000, proxying `/api`, `/outputs`, `/uploads` to the backend); desktop is not containerised.

## Commands

### One-shot (Linux)

```bash
./run.sh    # backend :8000 + Vite :3000 + Electron; kills the services when Electron exits
```

Override with `BACKEND_PORT`, `FRONTEND_PORT`, `PYTHON`. `setup_and_run.bat` is the Windows equivalent.

### Manual dev (run each in its own shell, in this order)

```bash
# 1) Backend (FastAPI + AI workers)
cd backend
python3.12 -m venv venv && source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --port 8000 --reload

# 2) Frontend (Vite dev server on :3000, proxies /api and /outputs to :8000)
cd frontend
npm install
npm run dev

# 3) Desktop (only after frontend is up)
cd desktop
npm install
npm start
```

### Other

```bash
# Backend
python test_pipeline.py   # assert-based self-check of the crop/caption/audio logic

# Frontend
npm run build      # tsc + vite build → frontend/dist
npm run lint       # eslint (flat config), --max-warnings 0
npm run preview    # serve built dist

# Desktop
npm run pack       # electron-builder → desktop/release

# Docker (backend + frontend only)
docker compose up --build
```

`backend/test_pipeline.py` is the only test file — plain asserts, no pytest. There is no frontend test suite; do not invent Vitest/Jest commands.

## Architecture

### Backend pipeline (`backend/app/`)

A single async job worker drives a fixed pipeline. Submitting a job via `POST /api/process` enqueues into `queue_manager.queue` and lazily spawns the worker task on first job. The worker runs heavy CPU work via `loop.run_in_executor` so the event loop stays responsive.

Per-job stages, in order (see [queue_manager.py](backend/app/queue_manager.py)):

1. **Transcribe** — `ai/transcriber.py` (faster-whisper) extracts a 16kHz mono WAV with FFmpeg, then produces word-level timings.
2. **Score moments** — `ai/moment_detector.py` scores overlapping windows on speech hooks, OpenCV frame-difference motion, scene cuts, and per-second RMS loudness read back from that same WAV. Weights come from `config.Settings` (`WEIGHT_AUDIO_PEAK`, `WEIGHT_VISUAL_MOTION`, `WEIGHT_SCENE_CHANGE`, `WEIGHT_SEMANTIC_HOOK`, summing to 1.0).
3. **Per clip** — `ai/speaker_tracker.py` (OpenCV Haar frontal-face) → `ai/reframer.py` builds a rolling-average crop track and emits an FFmpeg `crop` filter expression → `ai/caption_burner.py` writes a per-clip `.ass` → `ai/video_engine.py` calls FFmpeg to render the MP4 and optionally `remove_silence`.

`app/main.py` exposes `/`, `/api/health`, `/api/upload`, `/api/process`, `/api/status/{job_id}`, `/api/plugins`. All state is in-memory on `queue_manager.jobs` — restarting the backend drops job history.

Failures are loud by design: transcription, face tracking and scene analysis raise instead of substituting synthetic data, and a job whose clips all fail to render is marked `failed` rather than `completed` with an empty list.

### Filesystem contract

`config.py` resolves paths relative to `backend/app/..` and creates them on import:

- `backend/uploads/` — raw input MP4s saved by `/api/upload`, served at `/uploads/...`
- `backend/outputs/` — rendered shorts, served at `/outputs/...`
- `backend/temp/` — per-job `.ass` files and extracted WAVs
- `backend/plugins/` — third-party plugin drop-folder (distinct from `backend/app/plugins/`, the framework itself)

Docker mounts `uploads/`, `outputs/`, `temp/` plus a named `model-cache` volume for the Whisper download; if you add new persistent directories, update `docker-compose.yml` too.

### Plugin system

`app/plugins/manager.py` scans `settings.PLUGINS_DIR` on startup, dynamically imports every `*.py`, and instantiates any subclass of `BaseAIPlugin` (from `app/plugins/base.py`). A plugin must implement `plugin_name`, `plugin_type`, `initialize()`, and `execute(video_path, context)`. The plugin manager is loaded but the pipeline does not currently invoke plugins — they are only listed via `GET /api/plugins`. Wiring plugins into the pipeline is an open extension point.

### Frontend ↔ backend contract

- All frontend fetches are **relative** (`/api/health`, `/api/upload`, `/api/process`, `/api/status/{id}`, and `/outputs/...` for video). The Vite proxy handles dev; nginx handles Docker. Never reintroduce absolute `http://localhost:8000` URLs — they break the Docker path.
- Backend CORS is wide open (`allow_origins=["*"]`).
- The React app polls `/api/health` every 5s as a heartbeat and `/api/status/{job_id}` every 1.5s for progress.
- Each completed clip carries a `words` array (clip-relative timings) so `CaptionEditor` shows the real transcript.

### Config (env vars)

Set on the backend process (see [config.py](backend/app/config.py)):

- `HOST`, `PORT` — bind address
- `WHISPER_MODEL` — `tiny|base|small|medium|large-v3` (default `base`)
- `DEVICE` — `cpu|cuda` (docker-compose defaults to `cpu`; switch to `cuda` only with `nvidia-runtime`)

## Gotchas worth keeping

- **Python 3.12.** `python3` on PATH here is anaconda's 3.13; the venv must come from `/usr/bin/python3.12`. `run.sh` enforces this.
- **Console scripts are path-bound.** `venv/bin/uvicorn` embeds the venv's absolute path at creation time, so it breaks if the repo moves. `run.sh` uses `venv/bin/python -m uvicorn` for that reason.
- **`requests` is an undeclared faster-whisper dependency.** `faster-whisper==1.1.1` imports it but does not list it, and `huggingface_hub` 1.x no longer pulls it in — hence the explicit pin in `requirements.txt`.
- **Escape commas in filter expressions.** Crop expressions are embedded in an FFmpeg filtergraph, so commas inside `if(lt(t,…))` must be `\,`. Unescaped ones terminate the filter and every render dies with `No such filter: '0.60)'`.
- **`-ss` resets clip time to zero.** `reframer.generate_ffmpeg_crop_filter` takes a `clip_start` and emits clip-relative thresholds; absolute timestamps silently freeze the pan.
- **Crop dimensions must be even** for libx264 + yuv420p. `reframer` rounds down, and `video_engine` appends a `scale=trunc(iw/2)*2:trunc(ih/2)*2` guard for expression-based crops.
- **Moment windows overlap** (`step = window / 2`), so anything derived per-clip from the shared transcript must be **copied**, never mutated in place.
- **Caption font follows the script.** `caption_burner` picks `DejaVu Sans` for Latin and `Noto Naskh Arabic` for Arabic/Urdu — DejaVu misses Urdu glyphs and Noto Sans Arabic Bold drops the lam-alef ligature.
