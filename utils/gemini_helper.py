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

def check_gemini_api():
    """
    Gemini API에 간단한 요청을 보내 접근성을 확인합니다.
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        model.generate_content("test")
        return True, "Gemini API is accessible."
    except Exception as e:
        return False, f"Failed to access Gemini API: {e}"

def process_batch_with_gemini(tasks):
    """
    여러 작업을 순차적으로 Gemini API에 요청하고 진행 상황을 표시하며 결과를 반환합니다.
    
    Args:
        tasks (list): 각 항목이 {"id": "...", "task": "..."} 형태의 딕셔너리인 리스트
        
    Returns:
        list: 각 항목이 {"id": "...", "result": "..."} 형태의 딕셔너리인 리스트
    """
    model_name = load_gemini_model_from_config()
    model = genai.GenerativeModel(model_name)
    results = []
    total_tasks = len(tasks)

    for i, task in enumerate(tasks):
        try:
            # 진행 상황을 캐리지 리턴으로 출력
            print(f"Processing... {i + 1}/{total_tasks}", end='\r', flush=True)
            
            # Gemini API에 전달할 프롬프트 (기존 task가 프롬프트 역할)
            prompt = task["task"]
            response = model.generate_content(prompt)
            
            result_text = "".join([part.text for part in response.parts])
            results.append({"id": task["id"], "result": result_text})

        except Exception as e:
            # 에러 발생 시, 줄바꿈 후 에러 메시지 출력
            print(f"\nAn error occurred while processing task {task['id']}: {e}")
            results.append({"id": task["id"], "result": f"Error: {e}"})

    # 모든 작업 완료 후, 줄바꿈 및 완료 메시지 출력
    print(f"\nProcessing complete. {total_tasks}/{total_tasks}")
    return results
