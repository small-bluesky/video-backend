from pathlib import Path

from openai import OpenAI

from app.core.config import settings


def transcribe_audio(audio_path: str) -> str:
    client = OpenAI(
        api_key=settings.SILICONFLOW_API_KEY,
        base_url=settings.SILICONFLOW_BASE_URL,
    )

    path = Path(audio_path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    with open(path, "rb") as f:
        response = client.audio.transcriptions.create(
            model="FunAudioLLM/SenseVoiceSmall",
            file=f,
            response_format="text",
            language="zh",
        )

    return response.text if hasattr(response, "text") else str(response)
