"""딸깍 무비 - 프롬프트 한 줄로 영상 자동화

사용법:
    python main.py "영상 주제를 입력하세요"
    python main.py "인공지능의 역사" --duration 300
    python main.py "테스트" --test  # API 없이 테스트
    python main.py --setup  # API 키 설정
"""

import argparse
import sys
import os

from src.pipeline import DDalkkakPipeline


def setup_api_keys():
    """API 키 설정 마법사"""
    print("=" * 50)
    print("  DDalkkak Movie - API 키 설정")
    print("=" * 50)
    print()
    print("이 설정은 .env 파일에 저장됩니다.")
    print("(엔터를 누르면 기존 값 유지)")
    print()

    env_path = os.path.join(os.path.dirname(__file__), ".env")

    # 기존 .env 파일 읽기
    existing_keys = {}
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    existing_keys[key] = value

    # Anthropic API 키
    current_anthropic = existing_keys.get("ANTHROPIC_API_KEY", "")
    masked_anthropic = current_anthropic[:10] + "..." if len(current_anthropic) > 10 else "(미설정)"
    print(f"[1] Anthropic API 키 (대본 생성용)")
    print(f"    현재: {masked_anthropic}")
    new_anthropic = input("    새 키 입력: ").strip()
    if new_anthropic:
        existing_keys["ANTHROPIC_API_KEY"] = new_anthropic
    print()

    # Gemini API 키
    current_gemini = existing_keys.get("GEMINI_API_KEY", "")
    masked_gemini = current_gemini[:10] + "..." if len(current_gemini) > 10 else "(미설정)"
    print(f"[2] Google Gemini API 키 (이미지 생성용)")
    print(f"    현재: {masked_gemini}")
    new_gemini = input("    새 키 입력: ").strip()
    if new_gemini:
        existing_keys["GEMINI_API_KEY"] = new_gemini
    print()

    # OpenAI API 키 (선택)
    current_openai = existing_keys.get("OPENAI_API_KEY", "")
    masked_openai = current_openai[:10] + "..." if len(current_openai) > 10 else "(미설정)"
    print(f"[3] OpenAI API 키 (선택 - DALL-E 이미지 생성용)")
    print(f"    현재: {masked_openai}")
    new_openai = input("    새 키 입력: ").strip()
    if new_openai:
        existing_keys["OPENAI_API_KEY"] = new_openai
    print()

    # .env 파일 저장
    with open(env_path, "w", encoding="utf-8") as f:
        f.write("# DDalkkak Movie - API Keys\n\n")
        f.write("# Anthropic (Claude) API - 대본 생성\n")
        f.write(f"ANTHROPIC_API_KEY={existing_keys.get('ANTHROPIC_API_KEY', '')}\n\n")
        f.write("# Google Gemini API - 이미지 생성\n")
        f.write(f"GEMINI_API_KEY={existing_keys.get('GEMINI_API_KEY', '')}\n\n")
        f.write("# OpenAI API (선택) - DALL-E 이미지 생성\n")
        openai_key = existing_keys.get('OPENAI_API_KEY', '')
        if openai_key:
            f.write(f"OPENAI_API_KEY={openai_key}\n")
        else:
            f.write("# OPENAI_API_KEY=your_openai_api_key_here\n")

    print("=" * 50)
    print("API 키가 저장되었습니다!")
    print("=" * 50)
    print()

    # 설정 확인
    print("현재 설정:")
    if existing_keys.get("ANTHROPIC_API_KEY"):
        print("  - Anthropic API: 설정됨")
    else:
        print("  - Anthropic API: 미설정 (대본 생성 불가)")

    if existing_keys.get("GEMINI_API_KEY"):
        print("  - Gemini API: 설정됨")
    else:
        print("  - Gemini API: 미설정")

    if existing_keys.get("OPENAI_API_KEY"):
        print("  - OpenAI API: 설정됨")
    else:
        print("  - OpenAI API: 미설정")

    print()
    return True


def main():
    parser = argparse.ArgumentParser(
        description="딸깍 무비 - 프롬프트 한 줄로 영상 자동화"
    )
    parser.add_argument("prompt", nargs="?", help="영상 주제/요청")
    parser.add_argument(
        "--duration", "-d", type=int, default=180, help="목표 영상 길이 (초, 기본: 180)"
    )
    parser.add_argument(
        "--image-provider",
        "-i",
        choices=["auto", "gemini", "openai", "placeholder"],
        default="auto",
        help="이미지 생성 제공자 (기본: auto)",
    )
    parser.add_argument("--output", "-o", help="출력 파일명")
    parser.add_argument(
        "--test", "-t", action="store_true", help="테스트 모드 (API 없이 실행)"
    )
    parser.add_argument(
        "--no-subtitles", action="store_true", help="자막 비활성화"
    )
    parser.add_argument(
        "--no-transitions", action="store_true", help="장면 전환 효과 비활성화"
    )
    parser.add_argument(
        "--setup", action="store_true", help="API 키 설정"
    )
    parser.add_argument(
        "--resolution", "-r",
        choices=["720p", "1080p", "1440p", "4k"],
        default="1080p",
        help="영상 해상도 (기본: 1080p)"
    )

    args = parser.parse_args()

    # API 키 설정 모드
    if args.setup:
        setup_api_keys()
        return

    # 프롬프트 입력
    if args.prompt:
        prompt = args.prompt
    else:
        print("=" * 40)
        print("  DDalkkak Movie")
        print("  프롬프트 한 줄로 영상 자동화")
        print("=" * 40)
        print()
        print("Tip: python main.py --setup 으로 API 키 설정")
        print()
        prompt = input("영상 주제를 입력하세요: ")

    if not prompt.strip():
        print("오류: 프롬프트를 입력해주세요.")
        sys.exit(1)

    print(f"\n프롬프트: {prompt}")
    print(f"목표 길이: {args.duration}초")
    print(f"해상도: {args.resolution}")
    if args.test:
        print("모드: 테스트 (API 미사용)")
    print()

    # 파이프라인 실행
    try:
        pipeline = DDalkkakPipeline(
            image_provider=args.image_provider,
            target_duration=args.duration,
            test_mode=args.test,
            enable_subtitles=not args.no_subtitles,
            enable_transitions=not args.no_transitions,
            resolution=args.resolution,
        )
        pipeline.create(prompt, args.output)

    except KeyboardInterrupt:
        print("\n취소됨")
        sys.exit(0)
    except Exception as e:
        print(f"\n오류 발생: {e}")
        raise


if __name__ == "__main__":
    main()
