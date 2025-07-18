# utils/gemini_helper.py
# Google AI (Gemini) API 관련 함수들을 포함합니다.

import google.generativeai as genai
from .file_helper import load_api_key

GEMINI_API_KEY = load_api_key("myapi")
genai.configure(api_key=GEMINI_API_KEY)

def process_text_with_gemini(transcript, user_prompt):
    """
    스크립트와 사용자 프롬프트를 조합하여 Gemini API에 요청하고,
    가공된 텍스트 결과를 반환합니다.
    """
    model = genai.GenerativeModel('gemini-1.5-flash')

    # 최종 프롬프트 구성
    prompt = f"""
    {user_prompt}

    --- 원본 스크립트 ---
    {transcript}
    --- 원본 스크립트 끝 ---
    """

    response = model.generate_content(prompt)
    return response.text
