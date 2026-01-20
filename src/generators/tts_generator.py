"""TTS 생성기 - 텍스트를 음성으로 변환"""

from pathlib import Path
from typing import Tuple

from gtts import gTTS
from mutagen.mp3 import MP3

from ..config import TEMP_DIR, TTS_LANGUAGE, TTS_SLOW


class TTSGenerator:
    """Google TTS를 사용한 음성 생성기"""

    def __init__(self, language: str = TTS_LANGUAGE, slow: bool = TTS_SLOW):
        self.language = language
        self.slow = slow

    def generate(self, text: str, scene_number: int) -> Tuple[Path, float]:
        """
        텍스트를 음성으로 변환

        Args:
            text: 나레이션 텍스트
            scene_number: 장면 번호

        Returns:
            (오디오 파일 경로, 길이(초))
        """
        output_path = TEMP_DIR / f"audio_{scene_number:03d}.mp3"

        # TTS 생성
        tts = gTTS(text=text, lang=self.language, slow=self.slow)
        tts.save(str(output_path))

        # 오디오 길이 계산
        audio = MP3(str(output_path))
        duration = audio.info.length

        return output_path, duration


if __name__ == "__main__":
    # 테스트
    gen = TTSGenerator()
    path, duration = gen.generate("안녕하세요, 딸깍 무비 테스트입니다.", 1)
    print(f"오디오 생성됨: {path} (길이: {duration:.2f}초)")
