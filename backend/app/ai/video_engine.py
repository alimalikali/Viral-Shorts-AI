import os
import re
import subprocess
from typing import List

class VideoEngine:
    def __init__(self):
        pass

    def run_ffmpeg(self, args: List[str]) -> bool:
        """Executes a list of FFmpeg CLI arguments."""
        command = ["ffmpeg", "-y"] + args
        try:
            print(f"Executing: {' '.join(command)}")
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg command failed. Error output:\n{e.stderr.decode(errors='ignore')}")
            return False

    def render_short_clip(
        self,
        video_path: str,
        start_time: float,
        end_time: float,
        output_path: str,
        aspect_ratio: str = "9:16",
        crop_filter: str = "",
        ass_path: str = "",
        use_blurred_bg: bool = False
    ) -> bool:
        """
        Processes a video clip with optional reframing crops, blurred background layouts,
        and burned subtitle tracks in a single unified command for speed.
        """
        args = []
        
        # Seek first for lightning fast cutting
        args += ["-ss", str(start_time), "-to", str(end_time), "-i", video_path]
        
        filter_complex = []
        video_output_label = "[v]"

        # libx264 with yuv420p rejects odd dimensions, and crop expressions can produce them
        even = "scale=trunc(iw/2)*2:trunc(ih/2)*2"

        # Base filter building
        if aspect_ratio == "9:16":
            if use_blurred_bg:
                # Blurred background filtergraph:
                # 1. Split input into back and front
                # 2. Scale back to 1080x1920, boxblur it
                # 3. Scale front to fit width (1080x607), overlay in center of back
                filter_complex.append(
                    "[0:v]split=2[bg_src][fg_src];"
                    "[bg_src]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:5[bg];"
                    "[fg_src]scale=1080:-1[fg];"
                    "[bg][fg]overlay=(W-w)/2:(H-h)/2[combined_v]"
                )
                video_output_label = "[combined_v]"
            elif crop_filter:
                # Dynamic panning crop filter supplied by reframer
                filter_complex.append(f"[0:v]{crop_filter},{even}[cropped_v]")
                video_output_label = "[cropped_v]"
            else:
                # Default centered crop from 16:9 to 9:16
                filter_complex.append(f"[0:v]crop=ih*9/16:ih:(in_w-out_w)/2:0,{even}[centered_v]")
                video_output_label = "[centered_v]"
        elif aspect_ratio == "1:1":
            # Crop to square
            filter_complex.append(f"[0:v]crop=ih:ih:(in_w-out_w)/2:0,{even}[square_v]")
            video_output_label = "[square_v]"
        elif aspect_ratio == "16:9":
            # Centered crop to landscape; a no-op on footage that is already 16:9
            filter_complex.append(f"[0:v]crop=iw:iw*9/16:0:(in_h-out_h)/2,{even}[wide_v]")
            video_output_label = "[wide_v]"


        # Add subtitles filter if ASS file is supplied
        if ass_path and os.path.exists(ass_path):
            # Escape path for FFmpeg subtitles filter
            escaped_ass = ass_path.replace("\\", "/").replace(":", "\\:")
            # If we already have video filter components, pipe it
            if filter_complex:
                filter_complex.append(f"{video_output_label}subtitles='{escaped_ass}'[subbed_v]")
                video_output_label = "[subbed_v]"
            else:
                filter_complex.append(f"[0:v]subtitles='{escaped_ass}'[subbed_v]")
                video_output_label = "[subbed_v]"

        if filter_complex:
            # Combine all filters
            filter_str = ";".join(filter_complex)
            args += ["-filter_complex", filter_str, "-map", video_output_label]
        else:
            args += ["-map", "0:v"]
            
        args += ["-map", "0:a?", "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", output_path]
        
        return self.run_ffmpeg(args)

    def remove_silence(self, video_path: str, output_path: str, silence_threshold_db: float = -35.0, min_silence_dur: float = 0.5) -> bool:
        """
        Uses FFmpeg's silencedetect to analyze audio track, isolates speaking intervals,
        and stitches them back together, automating silence removal.
        """
        try:
            # First detect silences
            command = [
                "ffmpeg", "-i", video_path,
                "-af", f"silencedetect=noise={silence_threshold_db}dB:d={min_silence_dur}",
                "-f", "null", "-"
            ]
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            stderr_output = result.stderr.decode(errors='ignore')
            
            # Parse silence start/end times
            silence_starts = [float(x) for x in re.findall(r"silence_start: ([\d\.]+)", stderr_output)]
            silence_ends = [float(x) for x in re.findall(r"silence_end: ([\d\.]+)", stderr_output)]
            
            # If no silence detected or length mismatch, just copy
            if not silence_starts or len(silence_starts) != len(silence_ends):
                args = ["-i", video_path, "-c", "copy", output_path]
                return self.run_ffmpeg(args)
                
            # Get video duration
            cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", video_path]
            duration = float(subprocess.check_output(cmd).decode().strip())
            
            # Calculate active (sounded) intervals
            active_intervals = []
            current_start = 0.0
            
            for start, end in zip(silence_starts, silence_ends):
                if start > current_start + 0.1:
                    active_intervals.append((current_start, start))
                current_start = end
                
            if current_start + 0.1 < duration:
                active_intervals.append((current_start, duration))
                
            # Build complex filter to concat intervals
            # e.g., "[0:v]trim=start=0:end=5,setpts=PTS-STARTPTS[v0]; [0:a]atrim=start=0:end=5,asetpts=PTS-STARTPTS[a0]; ... [v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]"
            filter_parts = []
            concat_inputs = ""
            for idx, (start, end) in enumerate(active_intervals):
                filter_parts.append(f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS[v{idx}]")
                filter_parts.append(f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{idx}]")
                concat_inputs += f"[v{idx}][a{idx}]"
                
            filter_parts.append(f"{concat_inputs}concat=n={len(active_intervals)}:v=1:a=1[v][a]")
            filter_str = ";".join(filter_parts)
            
            args = [
                "-i", video_path,
                "-filter_complex", filter_str,
                "-map", "[v]", "-map", "[a]",
                "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-c:a", "aac",
                output_path
            ]
            return self.run_ffmpeg(args)
        except Exception as e:
            print(f"Auto silence remover failed ({str(e)}), copying instead.")
            args = ["-i", video_path, "-c", "copy", output_path]
            return self.run_ffmpeg(args)

video_engine = VideoEngine()
