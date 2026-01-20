"""데이터 모델 정의"""

from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path


@dataclass
class Scene:
    """영상의 한 장면"""
    scene_number: int
    narration: str  # 나레이션 텍스트
    image_prompt: str  # 이미지 생성용 프롬프트
    duration: Optional[float] = None  # 초 단위 (TTS 후 결정)
    image_path: Optional[Path] = None
    audio_path: Optional[Path] = None


@dataclass
class Script:
    """전체 대본"""
    title: str
    scenes: List[Scene] = field(default_factory=list)

    @property
    def total_scenes(self) -> int:
        return len(self.scenes)

    @property
    def total_duration(self) -> float:
        """총 영상 길이 (초)"""
        return sum(s.duration or 0 for s in self.scenes)


@dataclass
class VideoProject:
    """영상 프로젝트"""
    prompt: str  # 원본 사용자 프롬프트
    script: Optional[Script] = None
    output_path: Optional[Path] = None
    status: str = "created"  # created, scripting, generating, composing, done, error
