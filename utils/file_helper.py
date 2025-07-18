# utils/file_helper.py
# 파일 이름 생성 및 저장 등 파일 관련 처리 함수들을 포함합니다.

import os
import re
import json

def load_api_key(key_name="myapi", filepath="MYAPI.json"):
    """
    지정된 JSON 파일에서 API 키를 로드합니다.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 상위 디렉토리로 이동하여 MYAPI.json 찾기
    json_path = os.path.join(script_dir, "..", filepath) 
    
    if not os.path.exists(json_path):
        print(f"경고: {json_path} 파일을 찾을 수 없습니다.")
        return None
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get(key_name)
    except (json.JSONDecodeError, IOError) as e:
        print(f"경고: API 키 파일 로딩 실패 - {e}.")
        return None

def generate_filename_from_content(content):
    """
    내용의 첫 줄을 기반으로 'a-b-c' 형태의 파일명을 생성합니다.
    """
    if not content:
        return "untitled.md"
        
    # 내용의 첫 줄을 제목으로 가정 (마크다운 # 제거)
    first_line = content.strip().split('\n')[0]
    first_line = re.sub(r'^\s*#+\s*', '', first_line) # '# ' 같은 마크다운 제목 제거
    
    # 파일명으로 사용할 수 없는 문자 제거
    sanitized_title = re.sub(r'[\\/*?:"<>|]', "", first_line)
    
    # 공백 및 연속된 하이픈을 단일 하이픈으로 변경
    filename = re.sub(r'\s+', '-', sanitized_title)
    filename = re.sub(r'-+', '-', filename).strip('-')
    
    # 너무 길 경우 자르기
    filename = (filename[:50] + '..') if len(filename) > 50 else filename
    
    return f"{filename}.md" if filename else "untitled.md"

def save_as_obsidian_note(path, content):
    """
    지정된 경로에 가공된 내용을 마크다운 파일로 저장합니다.
    파일 이름은 내용에서 자동으로 생성됩니다.
    """
    if not os.path.isdir(path):
        os.makedirs(path)
        print(f"'{path}' 폴더를 생성했습니다.")

    filename = generate_filename_from_content(content)
    file_path = os.path.join(path, filename)

    # 파일명 중복 방지
    counter = 1
    while os.path.exists(file_path):
        base, ext = os.path.splitext(filename)
        # 이미 카운터가 붙어있으면 제거하고 새로 붙임
        base = re.sub(r'-\d+$', '', base)
        file_path = os.path.join(path, f"{base}-{counter}{ext}")
        counter += 1

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"파일 저장 완료: {file_path}")

