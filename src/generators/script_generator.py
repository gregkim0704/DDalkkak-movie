"""대본 생성기 - Claude API를 사용하여 프롬프트에서 대본 생성"""

import json
from typing import Optional

from ..config import ANTHROPIC_API_KEY
from ..models import Script, Scene


class ScriptGenerator:
    """프롬프트를 받아 영상 대본을 생성하는 클래스"""

    def __init__(self, api_key: Optional[str] = None, use_placeholder: bool = False):
        self.use_placeholder = use_placeholder
        if not use_placeholder:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=api_key or ANTHROPIC_API_KEY)
        else:
            self.client = None

    def generate(self, prompt: str, target_duration: int = 180) -> Script:
        """
        프롬프트로부터 대본 생성

        Args:
            prompt: 사용자의 영상 주제/요청
            target_duration: 목표 영상 길이 (초), 기본 3분

        Returns:
            Script 객체
        """
        # 장면 수 계산 (장면당 약 15-20초 기준)
        num_scenes = max(5, target_duration // 18)

        # 플레이스홀더 모드 (API 키 없이 테스트용)
        if self.use_placeholder:
            return self._generate_placeholder(prompt, num_scenes)

        system_prompt = """당신은 유튜브 설명 영상의 대본 작가입니다.
사용자의 요청을 받아 영상 대본을 JSON 형식으로 작성합니다.

출력 형식 (반드시 이 JSON 구조를 따르세요):
{
    "title": "영상 제목",
    "scenes": [
        {
            "scene_number": 1,
            "narration": "이 장면에서 읽을 나레이션 텍스트",
            "image_prompt": "이 장면을 표현할 이미지 생성 프롬프트 (영어로)"
        }
    ]
}

규칙:
1. narration은 자연스러운 한국어로 작성
2. image_prompt는 영어로, 구체적이고 시각적으로 표현
3. 각 장면의 나레이션은 15-25초 분량 (약 50-80자)
4. 전체적으로 기승전결 구조를 유지
5. JSON만 출력, 다른 텍스트 없이"""

        user_message = f"""다음 주제로 {num_scenes}개 장면의 영상 대본을 작성해주세요:

주제: {prompt}

목표 영상 길이: 약 {target_duration // 60}분"""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        # 응답 파싱
        response_text = response.content[0].text

        # JSON 추출 (코드 블록 안에 있을 수 있음)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        data = json.loads(response_text.strip())

        # Script 객체 생성
        scenes = [
            Scene(
                scene_number=s["scene_number"],
                narration=s["narration"],
                image_prompt=s["image_prompt"],
            )
            for s in data["scenes"]
        ]

        return Script(title=data["title"], scenes=scenes)

    def _generate_placeholder(self, prompt: str, num_scenes: int) -> Script:
        """테스트용 더미 대본 생성"""
        scenes = []
        for i in range(min(num_scenes, 5)):  # 테스트용으로 최대 5장면
            scenes.append(
                Scene(
                    scene_number=i + 1,
                    narration=f"이것은 '{prompt}'에 대한 {i + 1}번째 장면입니다. 테스트용 나레이션입니다.",
                    image_prompt=f"Scene {i + 1} about {prompt}, digital art, colorful",
                )
            )
        return Script(title=f"테스트: {prompt}", scenes=scenes)


if __name__ == "__main__":
    # 테스트
    generator = ScriptGenerator()
    script = generator.generate("인공지능의 역사와 미래")
    print(f"제목: {script.title}")
    print(f"장면 수: {script.total_scenes}")
    for scene in script.scenes:
        print(f"\n[장면 {scene.scene_number}]")
        print(f"나레이션: {scene.narration}")
        print(f"이미지: {scene.image_prompt}")
