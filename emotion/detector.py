"""
情绪检测核心模块
基于 MediaPipe Face Landmarker 的实时情绪分析

对外提供：
  - get_emotion(blendshapes)   -> (emotion_str, confidence)
  - create_landmarker(mode)    -> FaceLandmarker 实例
  - process_frame(...)         -> (emotion_str, confidence) 或 None
"""

import os
import mediapipe as mp

# ── MediaPipe 别名 ──────────────────────────────────────────────────────────
BaseOptions         = mp.tasks.BaseOptions
FaceLandmarker      = mp.tasks.vision.FaceLandmarker
FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
VisionRunningMode   = mp.tasks.vision.RunningMode

# 模型文件路径（相对于本文件的上级目录 models/）
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'face_landmarker.task')


# ── 情绪判定 ────────────────────────────────────────────────────────────────
def get_emotion(blendshapes) -> tuple[str, float]:
    """
    根据 MediaPipe blendshapes 分析情绪。

    策略：只使用在"平静基线"接近 0 的特征，避免个体差异误判。

    Returns:
        (情绪标签, 置信度)，无法判断时返回 ("Neutral :|", 0.0)
    """
    s = {b.category_name: b.score for b in blendshapes}

    # 【生气】眉头下压（平静时接近 0，可靠）
    brow_down = (s.get('browDownLeft', 0) + s.get('browDownRight', 0)) / 2
    # 取两眼 squint 的较小值，避免单侧天然偏高误判（如戴眼镜）
    eye_squint_reliable = min(s.get('eyeSquintLeft', 0), s.get('eyeSquintRight', 0))

    # 【悲伤】嘴角下撇（不使用 browInnerUp，个体差异过大）
    mouth_frown = (s.get('mouthFrownLeft', 0) + s.get('mouthFrownRight', 0)) / 2

    # 【高兴】嘴角上扬
    mouth_smile = (s.get('mouthSmileLeft', 0) + s.get('mouthSmileRight', 0)) / 2

    # 【惊讶】张嘴 + 眼睛睁大
    jaw_open = s.get('jawOpen', 0)
    eye_wide = (s.get('eyeWideLeft', 0) + s.get('eyeWideRight', 0)) / 2

    # ── 计算各情绪得分 ──────────────────────────────────────────────────────
    # 生气：必须有眉头下压才激活
    angry_score = (
        3.0 * brow_down + 0.8 * eye_squint_reliable + 0.4 * mouth_frown
    ) if brow_down > 0.12 else 0.0

    sad_score     = 3.0 * mouth_frown
    happy_score   = 2.5 * mouth_smile
    surprise_score = 2.0 * jaw_open + 0.5 * eye_wide

    scores = {
        "Angry >_<": angry_score,
        "Sad  :(":   sad_score,
        "Happy :)":  happy_score,
        "Surprise!": surprise_score,
    }

    emotion    = max(scores, key=scores.get)
    confidence = scores[emotion]

    return (emotion, confidence) if confidence > 0.25 else ("Neutral :|", 0.0)


# ── MediaPipe 初始化 ─────────────────────────────────────────────────────────
def create_landmarker(mode=VisionRunningMode.VIDEO):
    """
    创建 FaceLandmarker 实例。

    Args:
        mode: VisionRunningMode.VIDEO（默认）/ IMAGE / LIVE_STREAM
    Returns:
        FaceLandmarker 上下文管理器，使用 `with create_landmarker() as lm:` 调用
    """
    options = FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=mode,
        output_face_blendshapes=True,
        num_faces=1,
    )
    return FaceLandmarker.create_from_options(options)


# ── 单帧处理 ─────────────────────────────────────────────────────────────────
def process_frame(landmarker, frame, timestamp_ms: int):
    """
    处理单帧图像并返回情绪结果。

    Args:
        landmarker:    FaceLandmarker 实例
        frame:         OpenCV BGR 格式 numpy 数组
        timestamp_ms:  当前帧时间戳（毫秒），VIDEO 模式下必须单调递增
    Returns:
        (emotion_str, confidence) 或 None（未检测到人脸时）
    """
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
    result = landmarker.detect_for_video(mp_image, timestamp_ms)
    if result and result.face_blendshapes:
        return get_emotion(result.face_blendshapes[0])
    return None
