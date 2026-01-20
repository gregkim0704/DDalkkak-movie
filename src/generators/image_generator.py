"""이미지 생성기 - 다양한 이미지 생성 API 지원"""

import urllib.request
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from ..config import OPENAI_API_KEY, TEMP_DIR
import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


class ImageGeneratorBase(ABC):
    """이미지 생성기 추상 클래스"""

    @abstractmethod
    def generate(self, prompt: str, output_path: Path) -> Path:
        """프롬프트로 이미지 생성"""
        pass


class OpenAIImageGenerator(ImageGeneratorBase):
    """OpenAI DALL-E 이미지 생성기"""

    def __init__(self, api_key: Optional[str] = None):
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key or OPENAI_API_KEY)

    def generate(
        self,
        prompt: str,
        output_path: Path,
        size: str = "1792x1024",
        quality: str = "standard",
    ) -> Path:
        """
        DALL-E로 이미지 생성

        Args:
            prompt: 이미지 생성 프롬프트
            output_path: 저장할 경로
            size: 이미지 크기 (1024x1024, 1792x1024, 1024x1792)
            quality: 품질 (standard, hd)
        """
        response = self.client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality=quality,
            n=1,
        )

        image_url = response.data[0].url

        # 이미지 다운로드
        urllib.request.urlretrieve(image_url, str(output_path))

        return output_path


class GeminiImageGenerator(ImageGeneratorBase):
    """Google Gemini 이미지 생성기"""

    def __init__(self, api_key: Optional[str] = None):
        from google import genai

        self.client = genai.Client(api_key=api_key or GEMINI_API_KEY)

    def generate(self, prompt: str, output_path: Path) -> Path:
        """
        Gemini로 이미지 생성

        Args:
            prompt: 이미지 생성 프롬프트
            output_path: 저장할 경로
        """
        from google.genai import types

        # Gemini 2.0 Flash 이미지 생성 모델 사용
        response = self.client.models.generate_content(
            model="gemini-2.0-flash-exp-image-generation",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        # 응답에서 이미지 추출
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                    # 이미지 데이터 저장
                    image_data = part.inline_data.data
                    with open(output_path, "wb") as f:
                        f.write(image_data)
                    return output_path

        raise Exception("이미지 생성 실패 - 응답에 이미지가 없습니다")


class PlaceholderImageGenerator(ImageGeneratorBase):
    """테스트용 더미 이미지 생성기 (API 없이 테스트할 때 사용)"""

    # 장면별 다른 색상
    COLORS = [
        (70, 100, 150),   # 파란색
        (100, 70, 130),   # 보라색
        (60, 120, 80),    # 초록색
        (150, 80, 60),    # 주황색
        (120, 60, 100),   # 자주색
        (80, 130, 130),   # 청록색
        (140, 100, 60),   # 갈색
        (90, 90, 140),    # 연보라
    ]

    def generate(self, prompt: str, output_path: Path) -> Path:
        """간단한 플레이스홀더 이미지 생성"""
        from PIL import Image, ImageDraw
        import hashlib

        # 프롬프트 기반으로 색상 선택
        color_idx = int(hashlib.md5(prompt.encode()).hexdigest(), 16) % len(self.COLORS)
        bg_color = self.COLORS[color_idx]

        # 1920x1080 RGB 이미지 생성
        img = Image.new("RGB", (1920, 1080), color=bg_color)
        draw = ImageDraw.Draw(img)

        # 그라데이션 효과 (간단한 사각형들)
        for i in range(5):
            offset = i * 50
            lighter = tuple(min(255, c + 20 + i * 10) for c in bg_color)
            draw.rectangle([offset, offset, 1920 - offset, 1080 - offset], outline=lighter, width=2)

        # 프롬프트 텍스트 표시
        text = prompt[:60] + "..." if len(prompt) > 60 else prompt

        # 텍스트 배경
        draw.rectangle([80, 480, 1840, 600], fill=(0, 0, 0, 128))

        # 텍스트
        draw.text((100, 500), text, fill=(255, 255, 255))
        draw.text((100, 550), "[Placeholder Image]", fill=(180, 180, 180))

        img.save(output_path, "PNG")
        return output_path


class ImageGenerator:
    """이미지 생성기 팩토리 및 래퍼"""

    def __init__(self, provider: str = "auto"):
        """
        Args:
            provider: "openai", "gemini", "placeholder", 또는 "auto"
        """
        if provider == "auto":
            # API 키가 있으면 해당 서비스 사용, 없으면 플레이스홀더
            if GEMINI_API_KEY:
                self.generator = GeminiImageGenerator()
                self.provider = "gemini"
            elif OPENAI_API_KEY:
                self.generator = OpenAIImageGenerator()
                self.provider = "openai"
            else:
                self.generator = PlaceholderImageGenerator()
                self.provider = "placeholder"
        elif provider == "gemini":
            self.generator = GeminiImageGenerator()
            self.provider = "gemini"
        elif provider == "openai":
            self.generator = OpenAIImageGenerator()
            self.provider = "openai"
        else:
            self.generator = PlaceholderImageGenerator()
            self.provider = "placeholder"

    def generate(self, prompt: str, scene_number: int) -> Path:
        """
        이미지 생성

        Args:
            prompt: 이미지 프롬프트
            scene_number: 장면 번호 (파일명에 사용)

        Returns:
            생성된 이미지 경로
        """
        output_path = TEMP_DIR / f"scene_{scene_number:03d}.png"
        return self.generator.generate(prompt, output_path)


if __name__ == "__main__":
    # 테스트
    gen = ImageGenerator(provider="placeholder")
    path = gen.generate("A futuristic city at sunset", 1)
    print(f"이미지 생성됨: {path}")
