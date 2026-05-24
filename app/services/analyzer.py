from app.core.config import settings
from app.skills.loader import load_skill, build_prompt
from openai import OpenAI


def analyze_video(
    transcript: str,
    visual_analysis: str = "",
    platform: str = "unknown",
    duration: int = 0,
    title: str = "unknown",
) -> str:
    skill = load_skill("video-breakdown")

    variables = {
        "video_transcript": transcript,
        "visual_analysis": visual_analysis or "无视觉分析数据，请仅基于文字转录进行分析。",
        "platform": platform,
        "duration": str(duration),
        "title": title,
    }

    system_prompt = build_prompt(skill, variables)

    client = OpenAI(
        api_key=settings.SILICONFLOW_API_KEY,
        base_url=settings.SILICONFLOW_BASE_URL,
    )

    runtime = skill.get("runtime", {})

    response = client.chat.completions.create(
        model=settings.SILICONFLOW_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请拆解这条视频：{title}"},
        ],
        temperature=runtime.get("temperature", 0.7),
        max_tokens=runtime.get("max_tokens", 8000),
    )

    return response.choices[0].message.content
