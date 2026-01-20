"""딸깍 무비 - Streamlit 웹 UI"""

import streamlit as st
from pathlib import Path
import os
import sys

# Streamlit Cloud 환경 설정
if 'STREAMLIT_SHARING' in os.environ or '/mount/src' in os.getcwd():
    # Streamlit secrets에서 환경변수 로드
    if hasattr(st, 'secrets'):
        for key in ['ANTHROPIC_API_KEY', 'GEMINI_API_KEY', 'OPENAI_API_KEY']:
            if key in st.secrets:
                os.environ[key] = st.secrets[key]

# 프로젝트 루트를 경로에 추가
PROJECT_ROOT = Path(__file__).parent
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def load_env_keys():
    """현재 .env 파일에서 API 키 로드"""
    env_path = Path(__file__).parent / ".env"
    keys = {}
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    keys[key] = value
    return keys


def save_env_keys(keys: dict):
    """API 키를 .env 파일에 저장"""
    env_path = Path(__file__).parent / ".env"
    with open(env_path, "w", encoding="utf-8") as f:
        f.write("# DDalkkak Movie - API Keys\n\n")
        f.write("# Anthropic (Claude) API - 대본 생성\n")
        f.write(f"ANTHROPIC_API_KEY={keys.get('ANTHROPIC_API_KEY', '')}\n\n")
        f.write("# Google Gemini API - 이미지 생성\n")
        f.write(f"GEMINI_API_KEY={keys.get('GEMINI_API_KEY', '')}\n\n")
        f.write("# OpenAI API (선택) - DALL-E 이미지 생성\n")
        openai_key = keys.get('OPENAI_API_KEY', '')
        if openai_key:
            f.write(f"OPENAI_API_KEY={openai_key}\n")
        else:
            f.write("# OPENAI_API_KEY=your_openai_api_key_here\n")

    # 환경 변수도 업데이트
    for key, value in keys.items():
        if value:
            os.environ[key] = value


def mask_key(key: str) -> str:
    """API 키를 마스킹하여 표시"""
    if not key or len(key) < 10:
        return ""
    return key[:8] + "..." + key[-4:]


def main():
    st.set_page_config(
        page_title="딸깍 무비",
        page_icon="🎬",
        layout="wide"
    )

    st.title("🎬 딸깍 무비")
    st.subheader("프롬프트 한 줄로 영상 자동화")

    # 마지막 생성 영상 다운로드 (세션에 저장된 경우)
    if 'last_video' in st.session_state:
        with st.expander("📥 최근 생성 영상 다운로드", expanded=True):
            last_video = st.session_state['last_video']
            st.write(f"**{last_video['title']}**")
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.video(last_video['data'])
            with col_b:
                st.download_button(
                    label="📥 다운로드",
                    data=last_video['data'],
                    file_name=last_video['name'],
                    mime="video/mp4",
                    use_container_width=True,
                    type="primary",
                    key="header_download"
                )
            st.divider()

    # 사이드바 설정
    with st.sidebar:
        st.header("⚙️ 설정")

        # API 키 설정 섹션
        with st.expander("🔑 API 키 설정", expanded=False):
            current_keys = load_env_keys()

            st.caption("API 키는 .env 파일에 저장됩니다")

            # Anthropic API 키
            anthropic_key = st.text_input(
                "Anthropic API 키 (대본 생성)",
                value=current_keys.get("ANTHROPIC_API_KEY", ""),
                type="password",
                help="Claude API 키 - 대본 생성에 필요"
            )

            # Gemini API 키
            gemini_key = st.text_input(
                "Gemini API 키 (이미지 생성)",
                value=current_keys.get("GEMINI_API_KEY", ""),
                type="password",
                help="Google Gemini API 키 - 이미지 생성에 사용"
            )

            # OpenAI API 키
            openai_key = st.text_input(
                "OpenAI API 키 (선택)",
                value=current_keys.get("OPENAI_API_KEY", ""),
                type="password",
                help="DALL-E 이미지 생성에 사용 (선택사항)"
            )

            if st.button("💾 API 키 저장", use_container_width=True):
                new_keys = {
                    "ANTHROPIC_API_KEY": anthropic_key,
                    "GEMINI_API_KEY": gemini_key,
                    "OPENAI_API_KEY": openai_key,
                }
                save_env_keys(new_keys)
                st.success("API 키가 저장되었습니다!")
                st.rerun()

            # 현재 상태 표시
            st.divider()
            st.caption("현재 상태:")
            if current_keys.get("ANTHROPIC_API_KEY"):
                st.caption(f"✅ Anthropic: {mask_key(current_keys.get('ANTHROPIC_API_KEY', ''))}")
            else:
                st.caption("❌ Anthropic: 미설정")

            if current_keys.get("GEMINI_API_KEY"):
                st.caption(f"✅ Gemini: {mask_key(current_keys.get('GEMINI_API_KEY', ''))}")
            else:
                st.caption("❌ Gemini: 미설정")

            if current_keys.get("OPENAI_API_KEY"):
                st.caption(f"✅ OpenAI: {mask_key(current_keys.get('OPENAI_API_KEY', ''))}")
            else:
                st.caption("⬜ OpenAI: 미설정 (선택)")

        st.divider()

        # 영상 설정
        st.subheader("🎬 영상 설정")

        duration = st.slider(
            "영상 길이 (초)",
            min_value=30,
            max_value=600,
            value=180,
            step=30,
            help="목표 영상 길이를 설정합니다"
        )

        image_provider = st.selectbox(
            "이미지 생성 방식",
            options=["auto", "gemini", "openai", "placeholder"],
            index=0,
            help="auto: API 키가 있으면 자동 선택"
        )

        resolution = st.selectbox(
            "해상도",
            options=["720p", "1080p", "1440p", "4k"],
            index=1,
            help="4K는 파일 크기가 커지지만 화질이 뚜렷합니다"
        )

        st.divider()

        enable_subtitles = st.checkbox("자막 표시", value=True)
        enable_transitions = st.checkbox("장면 전환 효과", value=True)

        st.divider()

        test_mode = st.checkbox(
            "테스트 모드",
            value=False,
            help="API 없이 더미 데이터로 테스트"
        )

    # 메인 영역
    prompt = st.text_area(
        "영상 주제를 입력하세요",
        placeholder="예: 블랙홀의 신비, 인공지능의 역사, 기후변화의 원인...",
        height=100
    )

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        generate_btn = st.button("🎬 영상 생성", type="primary", use_container_width=True)

    # API 키 확인
    current_keys = load_env_keys()
    if not test_mode and not current_keys.get("ANTHROPIC_API_KEY"):
        st.warning("⚠️ Anthropic API 키가 설정되지 않았습니다. 사이드바에서 API 키를 설정하거나 테스트 모드를 사용하세요.")

    # 영상 생성
    if generate_btn:
        if not prompt.strip():
            st.error("프롬프트를 입력해주세요.")
            return

        if not test_mode and not current_keys.get("ANTHROPIC_API_KEY"):
            st.error("API 키를 먼저 설정해주세요.")
            return

        # 진행 상태 표시
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            # 지연 import (Streamlit Cloud 호환성)
            from src.pipeline import DDalkkakPipeline

            # 파이프라인 생성
            pipeline = DDalkkakPipeline(
                image_provider=image_provider,
                target_duration=duration,
                test_mode=test_mode,
                enable_subtitles=enable_subtitles,
                enable_transitions=enable_transitions,
                resolution=resolution,
            )

            # 1단계: 대본 생성
            status_text.text("📝 [1/4] 대본 생성 중...")
            progress_bar.progress(10)

            project_script = pipeline.script_gen.generate(prompt, duration)
            progress_bar.progress(25)

            st.info(f"📄 제목: {project_script.title}")
            st.info(f"📊 장면 수: {project_script.total_scenes}개")

            # 2단계: 이미지 생성
            status_text.text("🖼️ [2/4] 이미지 생성 중...")
            for i, scene in enumerate(project_script.scenes):
                scene.image_path = pipeline.image_gen.generate(
                    scene.image_prompt, scene.scene_number
                )
                progress = 25 + int((i + 1) / len(project_script.scenes) * 25)
                progress_bar.progress(progress)

            # 3단계: TTS 생성
            status_text.text("🎙️ [3/4] 음성 생성 중...")
            for i, scene in enumerate(project_script.scenes):
                scene.audio_path, scene.duration = pipeline.tts_gen.generate(
                    scene.narration, scene.scene_number
                )
                progress = 50 + int((i + 1) / len(project_script.scenes) * 25)
                progress_bar.progress(progress)

            # 4단계: 영상 합성
            status_text.text("🎬 [4/4] 영상 합성 중...")
            progress_bar.progress(80)

            output_path = pipeline.video_composer.compose(project_script)
            progress_bar.progress(100)

            status_text.text("✅ 완성!")

            # 결과 표시
            st.success(f"🎉 영상 생성 완료!")
            st.info(f"📄 제목: {project_script.title}")
            st.info(f"⏱️ 총 길이: {project_script.total_duration:.1f}초")

            # 영상 미리보기 및 다운로드
            if output_path.exists():
                # 영상 데이터를 세션에 저장 (다운로드용)
                with open(output_path, "rb") as f:
                    video_data = f.read()

                st.session_state['last_video'] = {
                    'data': video_data,
                    'name': output_path.name,
                    'title': project_script.title
                }

                # 영상 미리보기
                st.video(video_data)

                # 다운로드 버튼 (크게 표시)
                st.markdown("---")
                col_dl1, col_dl2, col_dl3 = st.columns([1, 2, 1])
                with col_dl2:
                    st.download_button(
                        label="📥 영상 다운로드 (MP4)",
                        data=video_data,
                        file_name=output_path.name,
                        mime="video/mp4",
                        use_container_width=True,
                        type="primary"
                    )

        except Exception as e:
            st.error(f"오류 발생: {e}")
            raise

    # 기존 영상 목록
    st.divider()
    st.subheader("📁 생성된 영상 목록")

    video_files = list(OUTPUT_DIR.glob("*.mp4"))
    if video_files:
        video_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        for video_file in video_files[:5]:  # 최근 5개만 표시
            col1, col2 = st.columns([3, 1])
            with col1:
                st.text(f"🎬 {video_file.name}")
            with col2:
                with open(video_file, "rb") as f:
                    st.download_button(
                        label="📥",
                        data=f,
                        file_name=video_file.name,
                        mime="video/mp4",
                        key=str(video_file)
                    )
    else:
        st.text("아직 생성된 영상이 없습니다.")


if __name__ == "__main__":
    main()
