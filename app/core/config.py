from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    SILICONFLOW_API_KEY: str = ""
    SILICONFLOW_BASE_URL: str = "https://api.siliconflow.cn/v1"
    SILICONFLOW_MODEL: str = "deepseek-ai/DeepSeek-V3"

    QIANWEN_API_KEY: str = ""
    QIANWEN_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    QIANWEN_VISION_MODEL: str = "qwen3.6-plus"

    TEMP_DIR: str = "./temp"
    MAX_VIDEO_SIZE_MB: int = 500
    DOWNLOAD_TIMEOUT: int = 120

    KEYFRAME_INTERVAL: int = 5
    KEYFRAME_MAX_COUNT: int = 15
    VISION_BATCH_SIZE: int = 5

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def temp_path(self) -> Path:
        p = Path(self.TEMP_DIR)
        p.mkdir(parents=True, exist_ok=True)
        return p


settings = Settings()
