import cv2
from typing import Dict, List, Any

class SpeakerTracker:
    def __init__(self):
        # Load OpenCV face detector safely
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

    def track_faces(self, video_path: str, start_time: float, end_time: float) -> List[Dict[str, Any]]:
        """
        Scans frames inside a timestamp range and detects face bounding boxes [x, y, w, h].
        Returns a list of frame positions with tracked coordinates.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"OpenCV could not open {video_path} for face tracking")

        tracking_data = []
        try:
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            cap.set(cv2.CAP_PROP_POS_MSEC, start_time * 1000.0)

            max_frames = int((end_time - start_time) * fps)
            # Subsample frames for speed (detect on every 5th, hold the focal point between)
            sample_rate = 5

            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            last_x = width / 2.0

            for frame_idx in range(max_frames):
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_idx % sample_rate == 0:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    # Downsample frame for fast Haar detection
                    small_gray = cv2.resize(gray, (0, 0), fx=0.5, fy=0.5)

                    faces = self.face_cascade.detectMultiScale(small_gray, 1.2, 4)
                    if len(faces) > 0:
                        # Largest detection is the closest speaker; scale back up
                        x, _, w, _ = max(faces, key=lambda f: f[2] * f[3])
                        last_x = (x + w / 2.0) * 2

                tracking_data.append({
                    "frame": frame_idx,
                    "timestamp": start_time + (frame_idx / fps),
                    "face_center_x": float(last_x),
                    "video_width": width,
                    "video_height": height
                })
        finally:
            cap.release()

        return tracking_data

speaker_tracker = SpeakerTracker()
