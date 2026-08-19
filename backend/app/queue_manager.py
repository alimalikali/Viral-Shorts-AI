import asyncio
import os
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, List
from app.config import settings
from app.ai.transcriber import transcriber
from app.ai.moment_detector import moment_detector
from app.ai.speaker_tracker import speaker_tracker
from app.ai.reframer import reframer
from app.ai.caption_burner import caption_burner
from app.ai.video_engine import video_engine

logger = logging.getLogger("QueueManager")

class QueueManager:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.worker_task = None

    def start_worker(self):
        """Launches the background queue listener."""
        if not self.worker_task:
            self.worker_task = asyncio.create_task(self._process_queue_worker())
            logger.info("Background queue worker started.")

    def submit_job(self, video_path: str, aspect_ratio: str = "9:16", style_name: str = "TikTok", remove_silence: bool = False) -> str:
        """Enqueues a new video processing job."""
        job_id = str(uuid.uuid4())
        self.jobs[job_id] = {
            "job_id": job_id,
            "video_path": video_path,
            "aspect_ratio": aspect_ratio,
            "style_name": style_name,
            "remove_silence": remove_silence,
            "status": "queued",
            "progress": 0,
            "clips": [],
            "error": None
        }
        self.queue.put_nowait(job_id)
        self.start_worker()
        return job_id

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Queries the status and rendering metadata of a job."""
        return self.jobs.get(job_id, {"status": "not_found"})

    async def _process_queue_worker(self):
        """Worker loop that dequeues and executes jobs one by one."""
        while True:
            job_id = await self.queue.get()
            job = self.jobs[job_id]
            job["status"] = "processing"
            job["progress"] = 5
            
            try:
                video_path = job["video_path"]
                aspect_ratio = job["aspect_ratio"]
                style_name = job["style_name"]
                
                # Step 1: Speech Transcription (Whisper)
                job["status"] = "transcribing"
                job["progress"] = 10
                logger.info(f"Job {job_id}: Beginning Whisper speech transcription...")
                
                # Run CPU/GPU heavy functions in threadpool to avoid blocking event loop
                loop = asyncio.get_running_loop()
                words = await loop.run_in_executor(None, transcriber.transcribe, video_path)
                
                job["progress"] = 40
                
                # Step 2: AI Moment Engagement Scoring
                job["status"] = "scoring_moments"
                job["progress"] = 45
                logger.info(f"Job {job_id}: Processing OpenCV histograms and engagement scoring...")
                
                clips = await loop.run_in_executor(None, moment_detector.analyze_viral_moments, video_path, words)
                
                job["progress"] = 60
                job["status"] = "rendering_clips"
                
                rendered_clips = []
                total_clips = len(clips)
                
                # Step 3: Face Tracking, Smart Crop & Caption Render for each short segment
                for idx, clip in enumerate(clips):
                    clip_id = clip["clip_id"]
                    start_t = clip["start"]
                    end_t = clip["end"]
                    
                    logger.info(f"Job {job_id}: Rendering clip {idx+1}/{total_clips} (range {start_t}s - {end_t}s)")
                    
                    # 3.1: Active Speaker Face Tracking
                    tracking_points = await loop.run_in_executor(
                        None, speaker_tracker.track_faces, video_path, start_t, end_t
                    )
                    
                    # 3.2: Reframe Crops & Compile Filter Expression
                    target_aspect = tuple(int(part) for part in aspect_ratio.split(":"))
                    crop_tracks = reframer.compute_crop_tracks(tracking_points, target_aspect)
                    crop_filter = reframer.generate_ffmpeg_crop_filter(crop_tracks, clip_start=start_t)

                    # 3.3: Filter words falling inside this clip and generate ASS Subtitles
                    # Copy, never mutate: clip windows overlap and share word dicts.
                    clip_words = [
                        {**w, "start": w["start"] - start_t, "end": w["end"] - start_t}
                        for w in words if start_t <= w["start"] <= end_t
                    ]

                    clip["words"] = clip_words

                    ass_path = str(Path(settings.TEMP_DIR) / f"{job_id}_{clip_id}.ass")
                    await loop.run_in_executor(
                        None, caption_burner.generate_ass_file, clip_words, ass_path, style_name
                    )
                    
                    # 3.4: Render out physical video with FFmpeg
                    out_filename = f"short_{job_id}_{clip_id}.mp4"
                    out_path = str(Path(settings.OUTPUT_DIR) / out_filename)
                    
                    render_success = await loop.run_in_executor(
                        None,
                        video_engine.render_short_clip,
                        video_path, start_t, end_t, out_path,
                        aspect_ratio, crop_filter, ass_path, False
                    )
                    
                    # If silence removal requested, clean the rendered clip
                    if job["remove_silence"] and render_success:
                        silence_removed_path = str(Path(settings.OUTPUT_DIR) / f"clean_{out_filename}")
                        clean_success = await loop.run_in_executor(
                            None, video_engine.remove_silence, out_path, silence_removed_path
                        )
                        if clean_success:
                            # Swap file paths
                            try:
                                os.remove(out_path)
                                os.rename(silence_removed_path, out_path)
                            except Exception:
                                pass
                                
                    if render_success:
                        # Append the visual asset URL path
                        clip["video_url"] = f"/outputs/{out_filename}"
                        rendered_clips.append(clip)
                        
                    # Increment progress
                    progress_share = 30.0 / total_clips
                    job["progress"] = int(60 + (progress_share * (idx + 1)))
                    
                job["clips"] = rendered_clips
                if not clips:
                    raise RuntimeError("No viral moments detected. The video may be too short or unreadable.")
                if not rendered_clips:
                    raise RuntimeError("FFmpeg failed to render every clip. See the backend log for its error output.")
                job["status"] = "completed"
                job["progress"] = 100
                logger.info(f"Job {job_id}: Processing queue pipeline completed successfully.")
                
            except Exception as e:
                logger.error(f"Job {job_id} failed with exception: {str(e)}")
                job["status"] = "failed"
                job["error"] = str(e)
            finally:
                self.queue.task_done()

queue_manager = QueueManager()
