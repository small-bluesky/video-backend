import re
import uuid
from pathlib import Path

import yt_dlp

from app.core.config import settings

_FFMPEG_PATH = None


def _get_ffmpeg_path() -> str | None:
    global _FFMPEG_PATH
    if _FFMPEG_PATH is not None:
        return _FFMPEG_PATH or None
    try:
        import imageio_ffmpeg
        _FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        _FFMPEG_PATH = ""
    return _FFMPEG_PATH or None


PLATFORM_PATTERNS = {
    "douyin": [r"douyin\.com", r"iesdouyin\.com"],
    "bilibili": [r"bilibili\.com", r"b23\.tv"],
    "xiaohongshu": [r"xiaohongshu\.com", r"xhslink\.com"],
}


def detect_platform(url: str) -> str:
    for platform, patterns in PLATFORM_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, url):
                return platform
    return "unknown"


def download_video(url: str) -> dict:
    platform = detect_platform(url)
    video_id = uuid.uuid4().hex[:12]
    output_dir = settings.temp_path / video_id
    output_dir.mkdir(parents=True, exist_ok=True)

    output_template = str(output_dir / "video.%(ext)s")

    ffmpeg_path = _get_ffmpeg_path()

    ydl_opts = {
        "outtmpl": output_template,
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "socket_timeout": settings.DOWNLOAD_TIMEOUT,
        "prefer_ffmpeg": True,
    }

    if ffmpeg_path:
        ydl_opts["ffmpeg_location"] = ffmpeg_path

    if platform == "bilibili":
        ydl_opts["writeautomaticsub"] = True
        ydl_opts["subtitleslangs"] = ["zh-Hans", "zh", "en"]
        ydl_opts["subtitle_format"] = "srt"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_title = info.get("title", "unknown")
        video_description = info.get("description", "")
        duration = info.get("duration", 0)

    video_path = _find_video(output_dir)
    subtitle_text = _find_subtitle(output_dir)

    if subtitle_text is None and video_description:
        subtitle_text = video_description

    return {
        "video_id": video_id,
        "platform": platform,
        "title": video_title,
        "description": video_description,
        "duration": duration,
        "video_path": str(video_path) if video_path else None,
        "subtitle_text": subtitle_text,
        "temp_dir": str(output_dir),
    }


def extract_audio(video_path: str) -> str | None:
    ffmpeg_path = _get_ffmpeg_path()
    if not ffmpeg_path:
        return None

    video = Path(video_path)
    output_dir = video.parent
    audio_output = str(output_dir / "audio.mp3")

    cmd = [
        ffmpeg_path,
        "-i", str(video),
        "-vn",
        "-acodec", "libmp3lame",
        "-q:a", "4",
        "-ar", "16000",
        "-y",
        audio_output,
    ]

    import subprocess
    try:
        subprocess.run(cmd, capture_output=True, timeout=60)
        if Path(audio_output).exists():
            return audio_output
    except Exception:
        pass

    return None


def _find_video(output_dir: Path) -> Path | None:
    video_exts = {".mp4", ".mkv", ".webm", ".avi", ".mov", ".flv"}
    for f in output_dir.iterdir():
        if f.suffix.lower() in video_exts:
            return f
    return None


def _find_subtitle(output_dir: Path) -> str | None:
    for f in output_dir.iterdir():
        if f.suffix in (".srt", ".vtt", ".ass"):
            return _parse_subtitle(f)
    return None


def _parse_subtitle(filepath: Path) -> str | None:
    try:
        content = filepath.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = filepath.read_text(encoding="gbk")

    lines = content.strip().split("\n")
    text_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.isdigit():
            continue
        if "-->" in line:
            continue
        if line.startswith("[") and line.endswith("]"):
            continue
        text_lines.append(line)

    return "\n".join(text_lines) if text_lines else None
