import subprocess
import json
from pathlib import Path

from app.core.config import settings


def _get_ffmpeg_bin() -> str:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def _get_ffprobe_bin() -> str:
    ffmpeg = _get_ffmpeg_bin()
    return ffmpeg.replace("ffmpeg", "ffprobe")


def extract_keyframes(video_path: str, output_dir: str | None = None) -> list[dict]:
    video = Path(video_path)
    if not video.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    if output_dir is None:
        output_dir = str(video.parent / "keyframes")
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    ffmpeg_bin = _get_ffmpeg_bin()
    duration = _get_duration(video, ffmpeg_bin)

    interval = settings.KEYFRAME_INTERVAL
    max_count = settings.KEYFRAME_MAX_COUNT

    if duration > 0:
        needed_interval = max(interval, duration / max_count)
    else:
        needed_interval = interval

    frame_pattern = str(out / "frame_%04d.jpg")

    cmd = [
        ffmpeg_bin,
        "-i", str(video),
        "-vf", f"fps=1/{needed_interval:.2f}",
        "-q:v", "2",
        "-y",
        frame_pattern,
    ]

    subprocess.run(cmd, capture_output=True, timeout=60)

    scene_frames = _extract_scene_changes(video, out, ffmpeg_bin)

    frames = sorted(out.glob("frame_*.jpg"))
    if not frames and not scene_frames:
        return []

    all_frames = _merge_frames(frames, scene_frames, needed_interval)

    result = []
    for i, (path, timestamp) in enumerate(all_frames):
        result.append({
            "index": i,
            "path": str(path),
            "timestamp": round(timestamp, 1),
            "timestamp_label": _format_timestamp(timestamp),
        })

    return result


def _get_duration(video_path: Path, ffmpeg_bin: str) -> float:
    ffprobe = ffmpeg_bin.replace("ffmpeg", "ffprobe")
    try:
        cmd = [
            ffprobe,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            str(video_path),
        ]
        output = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        info = json.loads(output.stdout)
        return float(info.get("format", {}).get("duration", 0))
    except Exception:
        return 0.0


def _extract_scene_changes(video_path: Path, out_dir: Path, ffmpeg_bin: str) -> list[tuple[Path, float]]:
    scene_pattern = str(out_dir / "scene_%04d.jpg")
    cmd = [
        ffmpeg_bin,
        "-i", str(video_path),
        "-vf", "select='gt(scene,0.3)',showinfo",
        "-vsync", "vfr",
        "-q:v", "2",
        "-y",
        scene_pattern,
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        timestamps = []
        for line in proc.stderr.split("\n"):
            if "showinfo" in line and "pts_time:" in line:
                try:
                    pts_part = line.split("pts_time:")[1].split(" ")[0]
                    timestamps.append(float(pts_part))
                except (ValueError, IndexError):
                    pass

        scene_files = sorted(out_dir.glob("scene_*.jpg"))
        result = []
        for i, f in enumerate(scene_files):
            ts = timestamps[i] if i < len(timestamps) else 0.0
            result.append((f, ts))

        return result
    except Exception:
        return []


def _merge_frames(
    interval_frames: list[Path],
    scene_frames: list[tuple[Path, float]],
    interval: float,
) -> list[tuple[Path, float]]:
    seen_timestamps = set()
    result = []

    for i, f in enumerate(interval_frames):
        ts = round(i * interval, 1)
        bucket = int(ts * 2)
        if bucket not in seen_timestamps:
            seen_timestamps.add(bucket)
            result.append((f, ts))

    for f, ts in scene_frames:
        bucket = int(ts * 2)
        if bucket not in seen_timestamps:
            seen_timestamps.add(bucket)
            result.append((f, ts))

    result.sort(key=lambda x: x[1])
    return result


def _format_timestamp(seconds: float) -> str:
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m}:{s:02d}"
