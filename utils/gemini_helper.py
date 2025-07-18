# utils/gemini_helper.py
# Google AI (Gemini) API 관련 함수들을 포함합니다.

import google.generativeai as genai
import json
import os
from .file_helper import load_api_key

GEMINI_API_KEY = load_api_key("myapi")
genai.configure(api_key=GEMINI_API_KEY)

def load_gemini_model_from_config():
    """config.json에서 사용할 Gemini 모델 이름을 로드합니다."""
    try:
        # 스크립트의 상위 디렉토리 (프로젝트 루트)를 기준으로 config.json 경로 설정
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, '..', 'config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get("gemini_model", "gemini-1.5-flash")
    except (FileNotFoundError, json.JSONDecodeError):
        return "gemini-1.5-flash" # 파일이 없거나 오류 발생 시 기본값

def process_text_with_gemini(transcript, user_prompt):
    """
    스크립트와 사용자 프롬프트를 조합하여 Gemini API에 요청하고,
    가공된 텍스트 결과를 반환합니다.
    """
    model_name = load_gemini_model_from_config()
    print(f"[Gemini] Using model: {model_name}") # 사용할 모델 이름 출력
    model = genai.GenerativeModel(model_name)

    # 최종 프롬프트 구성
    prompt = f"""
    {user_prompt}

    --- 원본 스크립트 ---
    {transcript}
    --- 원본 스크립트 끝 ---
    """

    response = model.generate_content(prompt)
    return response.text
