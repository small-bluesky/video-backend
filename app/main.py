from fastapi import FastAPI
from app.api.routes.analyze import router as analyze_router

app = FastAPI(
    title="Video Breakdown API",
    description="爆款视频拆解后端服务：输入视频URL，输出分镜拆解和爆款策略分析",
    version="1.0.0",
)

app.include_router(analyze_router)


@app.get("/")
async def root():
    return {"message": "Video Breakdown API is running", "docs": "/docs"}
