import numpy as np
from typing import List, Dict, Any, Tuple

class VideoReframer:
    def __init__(self, smoothing_window: int = 25):
        """
        :param smoothing_window: Size of moving average window in frames (approx 0.8s at 30fps)
        """
        self.smoothing_window = smoothing_window

    def compute_crop_tracks(self, tracking_points: List[Dict[str, Any]], target_aspect: Tuple[int, int] = (9, 16)) -> List[Dict[str, Any]]:
        """
        Calculates smoothed horizontal crop bounds for each frame.
        """
        if not tracking_points:
            return []
            
        width = tracking_points[0]["video_width"]
        height = tracking_points[0]["video_height"]
        
        # Calculate target crop box dimensions
        # Keep full height and scale width based on aspect ratio
        crop_height = height
        crop_width = int(height * (target_aspect[0] / target_aspect[1]))
        
        # Ensure crop width does not exceed source video width
        if crop_width > width:
            crop_width = width
            crop_height = int(width * (target_aspect[1] / target_aspect[0]))

        # libx264 with yuv420p rejects odd dimensions
        crop_width -= crop_width % 2
        crop_height -= crop_height % 2


        raw_x_coords = []
        for pt in tracking_points:
            raw_x_coords.append(pt["face_center_x"])
            
        # Apply padding moving average smoothing to coordinate paths
        smoothed_x = self._apply_moving_average(raw_x_coords, self.smoothing_window)
        
        crop_tracks = []
        for i, pt in enumerate(tracking_points):
            x_center = smoothed_x[i]
            
            # Constrain crop bounds inside video frame boundaries
            half_w = crop_width / 2.0
            left = x_center - half_w
            
            if left < 0:
                left = 0
            elif left + crop_width > width:
                left = width - crop_width
                
            crop_tracks.append({
                "frame": pt["frame"],
                "timestamp": pt["timestamp"],
                "crop_x": int(left),
                "crop_y": int((height - crop_height) / 2.0),
                "crop_w": crop_width,
                "crop_h": crop_height
            })
            
        return crop_tracks

    def generate_ffmpeg_crop_filter(self, crop_tracks: List[Dict[str, Any]], fps: float = 30.0, clip_start: float = 0.0) -> str:
        """
        Generates a compile-ready dynamic FFmpeg filter command mapping crop coordinates to time.
        Uses FFmpeg's conditional expressions to pan the crop window smoothly frame by frame.
        """
        if not crop_tracks:
            return ""
            
        crop_w = crop_tracks[0]["crop_w"]
        crop_h = crop_tracks[0]["crop_h"]
        
        # We compile the coordinates into an elegant ffmpeg 'crop' filter expression
        # crop=w:h:x:y
        # We can write an expression using time:
        # x='if(between(t, t0, t1), x0, if(between(t, t1, t2), x1, ...))'
        # To avoid exceeding command length limits, we chunk it into linear segments or step interpolations
        steps = []
        
        # Subsample to keep command line manageable (e.g. keyframe every 0.5s)
        sample_step = int(fps / 2) or 15
        
        for i in range(0, len(crop_tracks), sample_step):
            track = crop_tracks[i]
            # Timestamps are absolute, but ffmpeg's -ss resets clip time to zero
            t = track["timestamp"] - clip_start
            x = track["crop_x"]
            steps.append((t, x))

        # Add the final frame to close it off
        if (len(crop_tracks) - 1) % sample_step != 0:
            last = crop_tracks[-1]
            steps.append((last["timestamp"] - clip_start, last["crop_x"]))

        # Build nested conditional string
        # e.g., 'if(lt(t\, 1.5)\, 230\, if(lt(t\, 3.0)\, 280\, 310))'
        # Commas must be escaped or they terminate the filter in the filtergraph.
        expr_x = ""
        for t_val, x_val in reversed(steps):
            if not expr_x:
                expr_x = f"{x_val}"
            else:
                expr_x = f"if(lt(t\\,{t_val:.2f})\\,{x_val}\\,{expr_x})"

        return f"crop={crop_w}:{crop_h}:{expr_x}:(in_h-{crop_h})/2"

    def _apply_moving_average(self, data: List[float], window: int) -> List[float]:
        """Applies a zero-phase moving average filter using symmetric padding."""
        if len(data) <= window:
            return [sum(data)/len(data)] * len(data)
            
        padded_data = np.pad(data, (window // 2, window // 2), mode='edge')
        weights = np.ones(window) / window
        smoothed = np.convolve(padded_data, weights, mode='valid')
        
        # Trim back to original size
        return list(smoothed[:len(data)])

reframer = VideoReframer()
