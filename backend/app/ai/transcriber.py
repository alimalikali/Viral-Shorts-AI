import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any
from app.config import settings

class WhisperTranscriber:
    def __init__(self):
        self.model = None
        self.initialized = False

    def initialize(self):
        if self.initialized:
            return
        from faster_whisper import WhisperModel
        device = "cuda" if settings.DEVICE == "cuda" else "cpu"
        self.model = WhisperModel(settings.WHISPER_MODEL, device=device, compute_type="float32")
        self.initialized = True

    def audio_path(self, video_path: str) -> str:
        """Path of the WAV that extract_audio writes for a given video."""
        return str(Path(settings.TEMP_DIR) / f"{Path(video_path).stem}_temp_audio.wav")

    def extract_audio(self, video_path: str) -> str:
        """Extracts mono 16kHz WAV audio from a video using FFmpeg."""
        wav_path = self.audio_path(video_path)
        if os.path.exists(wav_path):
            try:
                os.remove(wav_path)
            except OSError:
                pass
                
        command = [
            "ffmpeg", "-y", "-i", video_path,
            "-vn", "-acodec", "pcm_s16le", "-ar", str(settings.SAMPLE_RATE), "-ac", "1",
            wav_path
        ]

        try:
            subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"FFmpeg audio extraction failed: {e.stderr.decode(errors='ignore')[-500:]}")
        except FileNotFoundError:
            raise RuntimeError("ffmpeg is not on PATH. Install it (apt install ffmpeg) and restart the backend.")
        return wav_path

    def transcribe(self, video_path: str) -> List[Dict[str, Any]]:
        """
        Transcribes the video and returns a list of word dictionaries with start/end timings.
        Format: [{'word': 'Hello', 'start': 0.1, 'end': 0.5, 'confidence': 0.9}]
        """
        self.initialize()
        wav_path = self.extract_audio(video_path)

        segments, _ = self.model.transcribe(wav_path, word_timestamps=True)
        return [
            {
                "word": word.word.strip(),
                "start": round(word.start, 3),
                "end": round(word.end, 3),
                "confidence": round(word.probability, 2)
            }
            for segment in segments
            for word in (segment.words or [])
        ]

transcriber = WhisperTranscriber()
