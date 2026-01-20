"""비디오 합성기 - 이미지와 오디오를 결합하여 영상 생성"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    concatenate_videoclips,
    CompositeVideoClip,
    TextClip,
)
import numpy as np

from ..config import OUTPUT_DIR, DEFAULT_VIDEO_WIDTH, DEFAULT_VIDEO_HEIGHT, DEFAULT_FPS
from ..models import Script, Scene


class VideoComposer:
    """이미지와 오디오를 결합하여 최종 영상 생성"""

    def __init__(
        self,
        width: int = DEFAULT_VIDEO_WIDTH,
        height: int = DEFAULT_VIDEO_HEIGHT,
        fps: int = DEFAULT_FPS,
        enable_subtitles: bool = True,
        enable_transitions: bool = True,
        transition_duration: float = 0.5,
    ):
        self.width = width
        self.height = height
        self.fps = fps
        self.enable_subtitles = enable_subtitles
        self.enable_transitions = enable_transitions
        self.transition_duration = transition_duration

    def _add_subtitle_to_image(self, img_array: np.ndarray, text: str) -> np.ndarray:
        """이미지에 자막 추가 (Pillow 사용)"""
        img = Image.fromarray(img_array)
        draw = ImageDraw.Draw(img)

        # 텍스트를 여러 줄로 나누기 (한 줄에 약 40자)
        max_chars_per_line = 40
        lines = []
        current_line = ""
        for char in text:
            current_line += char
            if len(current_line) >= max_chars_per_line and char in " .,!?。，！？":
                lines.append(current_line.strip())
                current_line = ""
        if current_line:
            lines.append(current_line.strip())

        # 최대 2줄로 제한
        if len(lines) > 2:
            lines = [lines[0], lines[1] + "..."]

        # 폰트 설정 (시스템 기본 폰트 사용)
        try:
            font = ImageFont.truetype("malgun.ttf", 36)  # Windows 맑은고딕
        except:
            try:
                font = ImageFont.truetype("NanumGothic.ttf", 36)  # 나눔고딕
            except:
                font = ImageFont.load_default()

        # 자막 영역 계산
        line_height = 45
        total_height = len(lines) * line_height
        y_start = self.height - total_height - 60  # 하단에서 60픽셀 위

        # 반투명 배경 그리기
        padding = 20
        bg_top = y_start - padding
        bg_bottom = self.height - 40
        draw.rectangle(
            [(0, bg_top), (self.width, bg_bottom)],
            fill=(0, 0, 0, 180)
        )

        # 텍스트 그리기 (그림자 효과)
        for i, line in enumerate(lines):
            # 텍스트 너비 계산
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2
            y = y_start + i * line_height

            # 그림자
            draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0))
            # 본문
            draw.text((x, y), line, font=font, fill=(255, 255, 255))

        return np.array(img)

    def _create_fade_effect(self, clip: ImageClip, fade_in: bool = True, fade_out: bool = True) -> ImageClip:
        """페이드 인/아웃 효과 적용"""
        if fade_in and self.transition_duration > 0:
            clip = clip.fadein(self.transition_duration)
        if fade_out and self.transition_duration > 0:
            clip = clip.fadeout(self.transition_duration)
        return clip

    def compose_scene(self, scene: Scene, is_first: bool = False, is_last: bool = False) -> ImageClip:
        """
        단일 장면을 비디오 클립으로 변환

        Args:
            scene: Scene 객체 (image_path, audio_path, duration 필요)
            is_first: 첫 번째 장면 여부 (페이드인만 적용)
            is_last: 마지막 장면 여부 (페이드아웃만 적용)

        Returns:
            ImageClip 객체
        """
        if not scene.image_path or not scene.audio_path:
            raise ValueError(f"장면 {scene.scene_number}에 이미지 또는 오디오가 없습니다")

        # 이미지 로드 및 리사이즈 (Pillow 사용 - moviepy resize 호환성 문제 회피)
        img = Image.open(str(scene.image_path))
        img = img.resize((self.width, self.height), Image.LANCZOS)
        img_array = np.array(img)

        # 자막 추가
        if self.enable_subtitles and scene.narration:
            img_array = self._add_subtitle_to_image(img_array, scene.narration)

        # 이미지 클립 생성
        image_clip = ImageClip(img_array)
        image_clip = image_clip.set_duration(scene.duration)

        # 페이드 효과 적용
        if self.enable_transitions:
            fade_in = is_first  # 첫 장면만 페이드인
            fade_out = is_last  # 마지막 장면만 페이드아웃
            image_clip = self._create_fade_effect(image_clip, fade_in=fade_in, fade_out=fade_out)

        # 오디오 추가
        audio_clip = AudioFileClip(str(scene.audio_path))
        image_clip = image_clip.set_audio(audio_clip)

        return image_clip

    def compose(self, script: Script, output_filename: str = None) -> Path:
        """
        전체 대본을 영상으로 합성

        Args:
            script: 완성된 Script 객체
            output_filename: 출력 파일명 (없으면 제목 사용)

        Returns:
            생성된 영상 파일 경로
        """
        # 각 장면을 클립으로 변환
        clips = []
        total_scenes = len(script.scenes)
        for i, scene in enumerate(script.scenes):
            is_first = (i == 0)
            is_last = (i == total_scenes - 1)
            clip = self.compose_scene(scene, is_first=is_first, is_last=is_last)
            clips.append(clip)

        # 클립들을 연결
        final_clip = concatenate_videoclips(clips, method="compose")

        # 출력 파일명 설정
        if output_filename is None:
            safe_title = "".join(
                c for c in script.title if c.isalnum() or c in (" ", "-", "_")
            ).strip()
            output_filename = f"{safe_title}.mp4"

        output_path = OUTPUT_DIR / output_filename

        # 영상 렌더링
        final_clip.write_videofile(
            str(output_path),
            fps=self.fps,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=str(OUTPUT_DIR / "temp_audio.m4a"),
            remove_temp=True,
        )

        # 리소스 정리
        final_clip.close()
        for clip in clips:
            clip.close()

        return output_path


if __name__ == "__main__":
    print("VideoComposer 모듈 - 직접 실행하려면 main.py를 사용하세요")
