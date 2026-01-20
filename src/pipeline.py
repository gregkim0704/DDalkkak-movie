"""메인 파이프라인 - 모든 생성기를 연결하여 영상 제작"""

from pathlib import Path
from typing import Optional

from .models import VideoProject, Script
from .generators import ScriptGenerator, ImageGenerator, TTSGenerator, VideoComposer
from .config import RESOLUTION_PRESETS


def log(msg: str):
    """Windows 호환 간단한 로그 출력"""
    print(msg)


class DDalkkakPipeline:
    """딸깍 무비 메인 파이프라인"""

    def __init__(
        self,
        image_provider: str = "auto",
        target_duration: int = 180,
        test_mode: bool = False,
        enable_subtitles: bool = True,
        enable_transitions: bool = True,
        resolution: str = "1080p",
    ):
        """
        Args:
            image_provider: 이미지 생성 제공자 ("openai", "placeholder", "auto")
            target_duration: 목표 영상 길이 (초), 기본 3분
            test_mode: True면 API 없이 더미 데이터로 테스트
            enable_subtitles: 자막 표시 여부
            enable_transitions: 장면 전환 효과 여부
            resolution: 해상도 ("720p", "1080p", "1440p", "4k")
        """
        # 해상도 설정
        width, height = RESOLUTION_PRESETS.get(resolution, RESOLUTION_PRESETS["1080p"])

        self.script_gen = ScriptGenerator(use_placeholder=test_mode)
        self.image_gen = ImageGenerator(provider="placeholder" if test_mode else image_provider)
        self.tts_gen = TTSGenerator()
        self.video_composer = VideoComposer(
            width=width,
            height=height,
            enable_subtitles=enable_subtitles,
            enable_transitions=enable_transitions,
        )
        self.target_duration = target_duration
        self.test_mode = test_mode
        self.resolution = resolution

    def create(self, prompt: str, output_filename: Optional[str] = None) -> Path:
        """
        프롬프트 하나로 영상 생성

        Args:
            prompt: 영상 주제/요청
            output_filename: 출력 파일명 (선택)

        Returns:
            생성된 영상 파일 경로
        """
        project = VideoProject(prompt=prompt)

        # 1. 대본 생성
        log("[1/4] 대본 생성 중...")
        project.status = "scripting"
        project.script = self.script_gen.generate(prompt, self.target_duration)
        log(f"  -> 대본 완성: {project.script.total_scenes}개 장면")
        log(f"  -> 제목: {project.script.title}")

        # 2. 이미지 생성
        log("[2/4] 이미지 생성 중...")
        project.status = "generating"
        for scene in project.script.scenes:
            scene.image_path = self.image_gen.generate(
                scene.image_prompt, scene.scene_number
            )
            log(f"  -> 장면 {scene.scene_number} 이미지 완료")

        # 3. TTS 생성
        log("[3/4] 음성 생성 중...")
        for scene in project.script.scenes:
            scene.audio_path, scene.duration = self.tts_gen.generate(
                scene.narration, scene.scene_number
            )
            log(f"  -> 장면 {scene.scene_number} 음성 완료 ({scene.duration:.1f}초)")

        # 4. 비디오 합성
        log("[4/4] 영상 합성 중...")
        project.status = "composing"
        project.output_path = self.video_composer.compose(
            project.script, output_filename
        )
        log("  -> 영상 합성 완료")

        project.status = "done"

        log("")
        log("=" * 40)
        log("완성!")
        log(f"총 길이: {project.script.total_duration:.1f}초")
        log(f"저장 위치: {project.output_path}")
        log("=" * 40)

        return project.output_path


def create_video(prompt: str, **kwargs) -> Path:
    """간편 함수: 프롬프트로 영상 생성"""
    pipeline = DDalkkakPipeline(**kwargs)
    return pipeline.create(prompt)
