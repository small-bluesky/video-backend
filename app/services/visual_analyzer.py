import base64
from pathlib import Path

from openai import OpenAI

from app.core.config import settings

VISUAL_ANALYSIS_PROMPT = """你是一位专业的短视频视觉分析师。你将看到一组从视频中按时间顺序抽取的关键帧截图。

请对每一帧进行以下维度的分析，并输出结构化结果：

## 逐帧分析
对每一帧，输出：
1. **时间码**：该帧对应的时间点
2. **景别**：特写/近景/中景/全景/远景
3. **构图**：居中/三分法/对角线/对称/留白
4. **画面内容**：描述画面中有什么（人物、物体、文字、背景）
5. **花字/字幕**：画面中出现的文字内容、位置、样式（大字报/底部字幕/贴纸文字/无）
6. **色调/滤镜**：暖色/冷色/高饱和/低饱和/黑白/复古/其他
7. **情绪氛围**：紧张/温馨/搞笑/震撼/平淡/其他
8. **视觉钩子**：该帧是否有视觉冲击力？用了什么手法（大字报/表情特写/闪切/对比/其他）

## 整体视觉分析
1. **视觉风格**：总结整个视频的视觉风格特征
2. **转场方式**：观察相邻帧之间的转场方式（硬切/缩放/遮挡/淡入淡出/其他）
3. **色彩剧本**：视频的色彩/色调是否有变化？变化与情绪的关系
4. **视觉节奏**：画面切换的快慢节奏，与内容节奏的配合
5. **前3秒视觉钩子**：视频前3秒的视觉策略（视觉冲击/悬念画面/反差画面/大字报/其他）
6. **文字设计规律**：花字/字幕的使用规律和设计风格

请严格按照以上格式输出，不要遗漏任何一帧。"""


def analyze_keyframes(keyframes: list[dict]) -> str:
    if not keyframes:
        return "无关键帧数据，跳过视觉分析。"

    client = OpenAI(
        api_key=settings.QIANWEN_API_KEY,
        base_url=settings.QIANWEN_BASE_URL,
    )

    batch_size = settings.VISION_BATCH_SIZE
    batches = _split_batches(keyframes, batch_size)

    if len(batches) == 1:
        return _analyze_single_batch(client, batches[0])

    parts = []
    for i, batch in enumerate(batches):
        part_result = _analyze_single_batch(client, batch, batch_index=i)
        parts.append(part_result)

    return _merge_visual_parts(parts)


def _analyze_single_batch(
    client: OpenAI, batch: list[dict], batch_index: int = 0
) -> str:
    content_parts = []

    if batch_index > 0:
        content_parts.append({
            "type": "text",
            "text": f"以下是视频的第 {batch_index + 1} 批关键帧（续前批）：",
        })
    else:
        content_parts.append({
            "type": "text",
            "text": VISUAL_ANALYSIS_PROMPT,
        })

    for frame in batch:
        image_b64 = _encode_image(frame["path"])
        if image_b64:
            content_parts.append({
                "type": "text",
                "text": f"[时间码 {frame['timestamp_label']}]",
            })
            content_parts.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image_b64}",
                },
            })

    response = client.chat.completions.create(
        model=settings.QIANWEN_VISION_MODEL,
        messages=[{"role": "user", "content": content_parts}],
        temperature=0.3,
        max_tokens=4000,
        extra_body={"enable_thinking": False},
    )

    return response.choices[0].message.content


def _encode_image(image_path: str) -> str | None:
    try:
        path = Path(image_path)
        if not path.exists():
            return None
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        return None


def _split_batches(items: list, batch_size: int) -> list[list]:
    return [items[i : i + batch_size] for i in range(0, len(items), batch_size)]


def _merge_visual_parts(parts: list[str]) -> str:
    header = "## 视觉分析报告（多批次合并）\n\n"
    return header + "\n\n---\n\n".join(parts)
