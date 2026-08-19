"""Self-check for the pieces of the pipeline that are easy to break silently.

Run with:  venv/bin/python test_pipeline.py
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from app.ai.caption_burner import caption_burner
from app.ai.moment_detector import moment_detector
from app.ai.reframer import reframer


def make_tracks(start_time, frames=90, fps=30.0, width=1920, height=1080):
    return [
        {
            "frame": i,
            "timestamp": start_time + i / fps,
            "face_center_x": 400.0 + i * 5,
            "video_width": width,
            "video_height": height,
        }
        for i in range(frames)
    ]


def test_crop_dimensions_are_even():
    tracks = reframer.compute_crop_tracks(make_tracks(0.0, width=1920, height=1081))
    assert tracks, "expected crop tracks"
    assert tracks[0]["crop_w"] % 2 == 0, tracks[0]
    assert tracks[0]["crop_h"] % 2 == 0, tracks[0]


def test_crop_filter_is_clip_relative_and_escaped():
    tracks = reframer.compute_crop_tracks(make_tracks(60.0))
    expr = reframer.generate_ffmpeg_crop_filter(tracks, clip_start=60.0)

    # Unescaped commas terminate the filter inside a filtergraph
    assert "\\," in expr, expr
    assert expr.replace("\\,", "") .count(",") == 0, expr

    # Thresholds must be clip-relative, i.e. within the clip's own duration
    thresholds = [float(chunk.split(")")[0]) for chunk in expr.split("lt(t\\,")[1:]]
    assert thresholds, expr
    assert max(thresholds) < 5.0, thresholds


def test_crop_filter_survives_ffmpeg():
    tracks = reframer.compute_crop_tracks(make_tracks(60.0))
    crop = reframer.generate_ffmpeg_crop_filter(tracks, clip_start=60.0)
    result = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-f", "lavfi",
            "-i", "testsrc=size=1920x1080:rate=30:duration=1",
            "-filter_complex", f"[0:v]{crop}[v]", "-map", "[v]", "-f", "null", "-",
        ],
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr.decode(errors="ignore")[-800:]


def test_audio_peaks_track_loudness():
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "tone.wav"
        subprocess.run(
            [
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-f", "lavfi", "-i", "sine=frequency=440:duration=3",
                "-af", "volume=0.05,volume=enable='between(t,1,2)':volume=20",
                "-ar", "16000", "-ac", "1", str(wav),
            ],
            check=True,
        )
        peaks = moment_detector._read_rms(str(wav))

    assert len(peaks) == 3, peaks
    loud = peaks[1][1]
    assert loud > peaks[0][1] and loud > peaks[2][1], peaks


def test_caption_font_follows_script():
    latin = [{"word": "Hello", "start": 0.0, "end": 0.4, "confidence": 1.0}]
    urdu = [{"word": "آپ", "start": 0.0, "end": 0.4, "confidence": 1.0}]

    with tempfile.TemporaryDirectory() as tmp:
        latin_path = Path(tmp) / "latin.ass"
        urdu_path = Path(tmp) / "urdu.ass"
        assert caption_burner.generate_ass_file(latin, str(latin_path))
        assert caption_burner.generate_ass_file(urdu, str(urdu_path))

        assert "DejaVu Sans" in latin_path.read_text(encoding="utf-8")
        assert "Noto Naskh Arabic" in urdu_path.read_text(encoding="utf-8")


def test_caption_timestamps_are_clip_relative():
    words = [{"word": "one", "start": 0.0, "end": 0.5, "confidence": 1.0}]
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "t.ass"
        caption_burner.generate_ass_file(words, str(path))
        dialogue = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.startswith("Dialogue")]

    assert dialogue, "expected at least one Dialogue line"
    assert dialogue[0].split(",")[1] == "0:00:00.00", dialogue[0]


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_"):
            continue
        try:
            fn()
            print(f"PASS {name}")
        except AssertionError as e:
            failures += 1
            print(f"FAIL {name}: {e}")
    sys.exit(1 if failures else 0)
