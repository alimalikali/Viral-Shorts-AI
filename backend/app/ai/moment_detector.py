import os
import wave
import cv2
import numpy as np
from typing import List, Dict, Any, Tuple
from app.config import settings
from app.ai.transcriber import transcriber

HOOK_WORDS = {
    "wait", "shocking", "amazing", "insane", "crazy", "never", "believe",
    "god", "shouting", "loud", "love", "hate", "secret"
}

TITLE_BY_HOOK = {
    "semantic": "Why did nobody tell me this? 🤫",
    "audio": "This moment is absolutely insane! 😱",
    "motion": "The ultimate hack you NEED! 🔥",
    "scene": "Wait for the ending... 🧠"
}

HOOK_LABEL = {
    "semantic": "Trending hook keyword match",
    "audio": "Unexpected speech emphasis",
    "motion": "High motion peak",
    "scene": "Rapid scene transitions"
}

HASHTAGS_BY_HOOK = {
    "semantic": "#shorts #viral #fyp #foryou #trending",
    "audio": "#viralshorts #omg #mindblown #fyp",
    "motion": "#ytshorts #satisfying #trending #capcut",
    "scene": "#tiktokviral #trendingreels #shorts #fyp"
}


class MomentDetector:
    def detect_scenes_and_peaks(self, video_path: str) -> Dict[str, List[Any]]:
        """
        Samples one frame per second with OpenCV and measures inter-frame difference,
        yielding a motion track and a list of scene-change timestamps.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"OpenCV could not open {video_path}")

        try:
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            step = max(1, int(round(fps)))

            scene_changes: List[float] = []
            visual_motion: List[Tuple[float, float]] = []

            prev = None
            frame_idx = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                gray = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (100, 100))
                if prev is not None:
                    mean_diff = float(np.mean(cv2.absdiff(gray, prev)))
                    timestamp = frame_idx / fps
                    visual_motion.append((timestamp, mean_diff))
                    if mean_diff > 45.0:
                        scene_changes.append(timestamp)
                prev = gray

                # grab() decodes nothing, so skipping ahead stays cheap and sequential
                for _ in range(step - 1):
                    if not cap.grab():
                        break
                frame_idx += step
        finally:
            cap.release()

        return {"scene_changes": scene_changes, "visual_motion": visual_motion}

    def detect_audio_peaks(self, video_path: str) -> List[Tuple[float, float]]:
        """
        Reads the 16kHz mono WAV the transcriber already extracted and returns
        per-second RMS loudness. Empty when the video carries no audio track.
        """
        wav_path = transcriber.audio_path(video_path)
        return self._read_rms(wav_path) if os.path.exists(wav_path) else []

    def _read_rms(self, wav_path: str) -> List[Tuple[float, float]]:
        """Per-second RMS of a mono PCM WAV."""
        with wave.open(wav_path, "rb") as wav:
            rate = wav.getframerate()
            samples = np.frombuffer(wav.readframes(wav.getnframes()), dtype=np.int16)

        if samples.size == 0:
            return []

        usable = samples.size - (samples.size % rate) or samples.size
        blocks = samples[:usable].astype(np.float32).reshape(-1, rate if usable >= rate else usable)
        rms = np.sqrt(np.mean(np.square(blocks), axis=1))
        return [(float(i), float(v)) for i, v in enumerate(rms)]

    def analyze_viral_moments(self, video_path: str, transcript: List[Dict[str, Any]], target_duration: int = 30) -> List[Dict[str, Any]]:
        """
        Scores overlapping windows on speech hooks, visual motion, scene cuts and audio
        loudness, weighted by settings.WEIGHT_*, and returns the top 5 moments.
        """
        visual_peaks = self.detect_scenes_and_peaks(video_path)
        audio_peaks = self.detect_audio_peaks(video_path)

        video_duration = max((w["end"] for w in transcript), default=0.0) + 2.0
        if visual_peaks["visual_motion"]:
            video_duration = max(video_duration, visual_peaks["visual_motion"][-1][0])

        window_size = min(float(target_duration), max(5.0, video_duration - 1.0))
        step_size = max(5, int(window_size / 2))

        motion_ceiling = max((m[1] for m in visual_peaks["visual_motion"]), default=0.0) or 1.0
        audio_ceiling = max((a[1] for a in audio_peaks), default=0.0) or 1.0

        candidates = []
        start_time = 0.0

        while start_time + window_size <= video_duration:
            end_time = start_time + window_size

            words_in_window = [w["word"] for w in transcript if start_time <= w["start"] <= end_time]
            hooks = sum(
                1 for w in words_in_window
                if w.lower().strip(".,!?;:()\"'") in HOOK_WORDS
            )
            semantic = min(1.0, hooks * 0.25 + len(words_in_window) * 0.005)

            motion_vals = [m[1] for m in visual_peaks["visual_motion"] if start_time <= m[0] <= end_time]
            motion = float(np.mean(motion_vals)) / motion_ceiling if motion_vals else 0.0

            cuts = sum(1 for c in visual_peaks["scene_changes"] if start_time <= c <= end_time)
            scene = min(1.0, cuts / 5.0)

            audio_vals = [a[1] for a in audio_peaks if start_time <= a[0] <= end_time]
            audio = float(np.max(audio_vals)) / audio_ceiling if audio_vals else 0.0

            contributions = {
                "semantic": settings.WEIGHT_SEMANTIC_HOOK * semantic,
                "motion": settings.WEIGHT_VISUAL_MOTION * motion,
                "scene": settings.WEIGHT_SCENE_CHANGE * scene,
                "audio": settings.WEIGHT_AUDIO_PEAK * audio
            }
            viral_score = int(round(100 * sum(contributions.values())))
            dominant = max(contributions, key=contributions.get)

            aligned_start, aligned_end = self._align_to_speech(transcript, start_time, end_time)
            if aligned_end - aligned_start < 5.0:
                aligned_end = aligned_start + window_size

            candidates.append({
                "clip_id": f"clip_{int(aligned_start)}_{int(aligned_end)}",
                "start": round(aligned_start, 2),
                "end": round(aligned_end, 2),
                "duration": round(aligned_end - aligned_start, 2),
                "viral_score": viral_score,
                "engagement_rating": "Very High" if viral_score > 70 else "High" if viral_score > 45 else "Medium",
                "retention_prediction": f"{min(99, 50 + viral_score // 2)}%",
                "suggested_title": TITLE_BY_HOOK[dominant],
                "suggested_hashtags": HASHTAGS_BY_HOOK[dominant],
                "suggested_caption": " ".join(words_in_window[:14]),
                "hook_type": HOOK_LABEL[dominant]
            })

            start_time += step_size

        return sorted(candidates, key=lambda c: c["viral_score"], reverse=True)[:5]

    def _align_to_speech(self, transcript: List[Dict[str, Any]], start_time: float, end_time: float) -> Tuple[float, float]:
        """Snaps window edges to the nearest spoken word boundary within 2s."""
        starts = [w["start"] for w in transcript if abs(w["start"] - start_time) <= 2.0]
        ends = [w["end"] for w in transcript if abs(w["end"] - end_time) <= 2.0]
        aligned_start = min(starts, key=lambda x: abs(x - start_time)) if starts else start_time
        aligned_end = min(ends, key=lambda x: abs(x - end_time)) if ends else end_time
        return aligned_start, aligned_end


moment_detector = MomentDetector()
