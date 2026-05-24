from pydantic import BaseModel, HttpUrl


class AnalyzeRequest(BaseModel):
    url: HttpUrl


class AnalyzeResponse(BaseModel):
    video_id: str
    platform: str
    title: str
    duration: int
    transcript: str
    visual_analysis: str = ""
    analysis: str
