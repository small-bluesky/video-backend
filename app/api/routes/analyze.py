import shutil

from fastapi import APIRouter, HTTPException

from app.models import AnalyzeRequest, AnalyzeResponse
from app.services.downloader import download_video, extract_audio
from app.services.keyframe import extract_keyframes
from app.services.transcriber import transcribe_audio
from app.services.visual_analyzer import analyze_keyframes
from app.services.analyzer import analyze_video

router = APIRouter(prefix="/api", tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    try:
        video_info = download_video(str(req.url))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"视频下载失败: {str(e)}")

    visual_analysis = ""
    video_path = video_info.get("video_path")
    if video_path:
        try:
            keyframes = extract_keyframes(video_path)
            if keyframes:
                visual_analysis = analyze_keyframes(keyframes)
        except Exception as e:
            visual_analysis = f"视觉分析跳过（原因: {str(e)}），将仅基于文字转录分析。"

    transcript = video_info.get("subtitle_text")

    if not transcript:
        audio_path = video_info.get("audio_path")
        if not audio_path and video_path:
            audio_path = extract_audio(video_path)

        if audio_path:
            try:
                transcript = transcribe_audio(audio_path)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"语音转录失败: {str(e)}")

    if not transcript:
        raise HTTPException(status_code=400, detail="无法获取视频文本内容")

    try:
        analysis = analyze_video(
            transcript=transcript,
            visual_analysis=visual_analysis,
            platform=video_info["platform"],
            duration=int(video_info.get("duration", 0) or 0),
            title=video_info.get("title", "unknown"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")

    try:
        temp_dir = video_info.get("temp_dir")
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception:
        pass

    return AnalyzeResponse(
        video_id=video_info["video_id"],
        platform=video_info["platform"],
        title=video_info.get("title", "unknown"),
        duration=int(video_info.get("duration", 0) or 0),
        transcript=transcript,
        visual_analysis=visual_analysis,
        analysis=analysis,
    )


@router.get("/health")
async def health():
    return {"status": "ok"}
