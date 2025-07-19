# main.py
# tkinter를 사용하여 GUI 애플리케이션을 생성하고 전체 프로세스를 제어합니다.

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import queue
import json
import os
from utils import youtube_helper, gemini_helper, file_helper

def load_config(filepath="config.json"):
    """JSON 파일에서 설정을 로드합니다."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, filepath)
    defaults = {
        "font_size": 12, 
        "theme": "dark",
        "obsidian_path": "C:/Users/bounc/OneDrive/문서/SummerVCT/Notes",
        "gemini_batch_size": 30,
        "youtube_url": "https://www.youtube.com/@slow_doctor",
        "min_video_duration": 120 # Default to 2 minutes (120 seconds)
    }

    if not os.path.exists(config_path):
        return defaults

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return {
                "font_size": config.get("font_size", defaults["font_size"]),
                "theme": config.get("theme", defaults["theme"]),
                "obsidian_path": config.get("obsidian_path", defaults["obsidian_path"]),
                "gemini_batch_size": config.get("gemini_batch_size", defaults["gemini_batch_size"]),
                "youtube_url": config.get("youtube_url", defaults["youtube_url"]),
                "min_video_duration": config.get("min_video_duration", defaults["min_video_duration"])
            }
    except (json.JSONDecodeError, IOError):
        return defaults

def load_prompt_from_json(filepath="default_prompt.json"):
    """JSON 파일에서 기본 프롬프트를 로드합니다."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, filepath)
    
    if not os.path.exists(json_path):
        print(f"경고: {json_path} 파일을 찾을 수 없습니다. 기본 프롬프트를 사용합니다.")
        return "다음 텍스트를 요약하고 정리해주세요:\n\n"
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("prompt", "다음 텍스트를 요약하고 정리해주세요:\n\n")
    except (json.JSONDecodeError, IOError) as e:
        print(f"경고: 프롬프트 파일 로딩 실패 - {e}. 기본 프롬프트를 사용합니다.")
        return "다음 텍스트를 요약하고 정리해주세요:\n\n"

# --- 기본 설정 ---
DEFAULT_PROMPT = load_prompt_from_json()
CONFIG = load_config()

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube 스크립트 분석기")
        self.geometry("1024x768")

        # --- UI 상태 변수 ---
        self.font_size = CONFIG['font_size']
        self.is_dark_mode = tk.BooleanVar(value=(CONFIG['theme'] == 'dark'))
        self.include_shorts = tk.BooleanVar(value=False)
        self.min_duration_seconds = tk.IntVar(value=CONFIG.get('min_video_duration', 120)) # Default to 120 seconds (2 minutes)
        
        # --- 스타일 설정 ---
        self.style = ttk.Style(self)
        self.update_styles()

        self.q = queue.Queue()
        self.after(100, self.process_queue)

        self.current_scene = None
        self.current_scene = self.create_scene1()
        self.update_styles() # 초기 다크모드 적용

    def update_styles(self):
        """UI의 폰트와 색상 테마를 업데이트합니다."""
        font_family = "Helvetica"
        current_font = (font_family, self.font_size)
        heading_font = (font_family, int(self.font_size * 1.2), "bold")

        if self.is_dark_mode.get():
            bg_color, fg_color, entry_bg, btn_bg, tree_bg, tree_heading_bg = "#2E2E2E", "#FFFFFF", "#3C3C3C", "#555555", "#3C3C3C", "#555555"
            self.configure(bg=bg_color)
            self.style.theme_use('clam')
        else:
            bg_color, fg_color, entry_bg, btn_bg, tree_bg, tree_heading_bg = "#F0F0F0", "#000000", "#FFFFFF", "#E1E1E1", "#FFFFFF", "#E1E1E1"
            self.configure(bg=bg_color)
            self.style.theme_use('default')

        self.style.configure('.', background=bg_color, foreground=fg_color, font=current_font)
        self.style.configure('TLabel', background=bg_color, foreground=fg_color)
        self.style.configure('TButton', background=btn_bg, foreground=fg_color, font=current_font)
        self.style.map('TButton', background=[('active', '#6E6E6E' if self.is_dark_mode.get() else '#C0C0C0')])
        self.style.configure('TEntry', fieldbackground=entry_bg, foreground=fg_color, insertcolor=fg_color)
        self.style.configure('Treeview', background=tree_bg, fieldbackground=tree_bg, foreground=fg_color, rowheight=self.font_size + 10)
        self.style.configure('Treeview.Heading', background=tree_heading_bg, foreground=fg_color, font=heading_font)
        self.style.map('Treeview.Heading', background=[('active', '#6E6E6E' if self.is_dark_mode.get() else '#D0D0D0')])

        if hasattr(self, 'prompt_text') and self.prompt_text.winfo_exists():
            self.prompt_text.config(bg=entry_bg, fg=fg_color, insertbackground=fg_color, font=current_font)
        
        if hasattr(self, 'progress_text') and self.progress_text.winfo_exists():
            self.progress_text.config(bg=entry_bg, fg=fg_color, font=current_font)
            
    def update_duration_label(self, *args):
        total_seconds = self.min_duration_seconds.get()
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        self.duration_label.config(text=f"{minutes}분 {seconds}초")

    def change_font_size(self, delta):
        new_size = self.font_size + delta
        if 8 <= new_size <= 24:
            self.font_size = new_size
            self.update_styles()
            
    def switch_scene(self, new_scene_creator, *args):
        if self.current_scene:
            self.current_scene.destroy()
        self.current_scene = new_scene_creator(*args)
        self.update_styles()

    def create_scene1(self):
        scene1 = ttk.Frame(self, padding=(20, 10))
        scene1.pack(fill="both", expand=True)

        control_frame = ttk.Frame(scene1)
        control_frame.pack(fill='x', pady=(0, 20))

        ttk.Button(control_frame, text="글씨 작게", command=lambda: self.change_font_size(-1)).pack(side="left", padx=5)
        ttk.Button(control_frame, text="글씨 크게", command=lambda: self.change_font_size(1)).pack(side="left", padx=5)
        ttk.Checkbutton(control_frame, text="다크 모드", variable=self.is_dark_mode, command=self.update_styles).pack(side="left", padx=10)
        ttk.Checkbutton(control_frame, text="Shorts 영상 포함", variable=self.include_shorts).pack(side="left", padx=10)

        # 최소 영상 길이 설정 (슬라이더)
        duration_frame = ttk.Frame(control_frame)
        duration_frame.pack(side="left", padx=10)
        ttk.Label(duration_frame, text="최소 영상 길이 (분):").pack(side="left")
        self.duration_slider = ttk.Scale(duration_frame, from_=0, to=60, orient="horizontal", variable=self.min_duration_seconds, command=self.update_duration_label)
        self.duration_slider.pack(side="left", padx=5)
        self.duration_label = ttk.Label(duration_frame, text="2분 0초")
        self.duration_label.pack(side="left")
        self.update_duration_label() # 초기값 설정

        main_content_frame = ttk.Frame(scene1)
        main_content_frame.pack(fill="both", expand=True)

        ttk.Label(main_content_frame, text="유튜브 채널 URL:").pack(pady=(0, 5), anchor='w')
        self.url_entry = ttk.Entry(main_content_frame)
        self.url_entry.pack(fill="x", pady=(0, 15))
        self.url_entry.insert(0, CONFIG.get('youtube_url', ''))

        ttk.Label(main_content_frame, text="Obsidian 저장 경로:").pack(pady=(0, 5), anchor='w')
        path_frame = ttk.Frame(main_content_frame)
        path_frame.pack(fill="x", pady=(0, 15))
        self.path_entry = ttk.Entry(path_frame)
        self.path_entry.pack(side="left", fill="x", expand=True)
        self.path_entry.insert(0, CONFIG.get('obsidian_path', ''))
        ttk.Button(path_frame, text="경로 선택", command=self.browse_path).pack(side="left", padx=(5, 0))

        ttk.Label(main_content_frame, text="Gemini 프롬프트:").pack(pady=(0, 5), anchor='w')
        self.prompt_text = scrolledtext.ScrolledText(main_content_frame, height=10, relief="solid", borderwidth=1)
        self.prompt_text.pack(fill="both", expand=True, pady=(0, 15))
        self.prompt_text.insert(tk.END, DEFAULT_PROMPT)

        self.confirm_btn1 = ttk.Button(main_content_frame, text="영상 목록 불러오기", command=self.start_fetching_videos)
        self.confirm_btn1.pack(pady=10, ipady=5)
        
        return scene1

    def browse_path(self):
        directory = filedialog.askdirectory()
        if directory:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, directory)

    def start_fetching_videos(self):
        self.channel_url = self.url_entry.get()
        self.obsidian_path = self.path_entry.get()
        self.user_prompt = self.prompt_text.get("1.0", tk.END)
        self.min_video_duration = self.min_duration_seconds.get()

        if not self.channel_url or not self.obsidian_path:
            messagebox.showerror("입력 오류", "채널 URL과 저장 경로는 필수입니다.")
            return

        self.confirm_btn1.config(state="disabled", text="불러오는 중...")
        threading.Thread(target=self.fetch_videos_thread, daemon=True).start()

    def fetch_videos_thread(self):
        try:
            self.all_videos = youtube_helper.get_videos_from_channel(self.channel_url, self.include_shorts.get(), self.min_video_duration)
            self.q.put(("videos_fetched", self.all_videos[:30]))
        except Exception as e:
            self.q.put(("error", f"영상 목록 로딩 실패: {e}"))

    def create_scene2(self, videos):
        scene2 = ttk.Frame(self, padding=(20, 20))
        scene2.pack(fill="both", expand=True)

        ttk.Label(scene2, text="처리할 영상을 선택하세요.", font=("Helvetica", int(self.font_size*1.3), "bold")).pack(pady=10, anchor='w')

        cols = ("제목", "영상 길이")
        self.tree = ttk.Treeview(scene2, columns=cols, show="headings")
        self.tree.heading("제목", text="영상 제목")
        self.tree.heading("영상 길이", text="영상 길이")
        self.tree.column("제목", width=600)
        self.tree.column("영상 길이", width=100, anchor='center')
        self.tree.pack(fill="both", expand=True, pady=10)

        scrollbar = ttk.Scrollbar(self.tree, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        for video in videos:
            self.tree.insert("", "end", values=(video['title'], video['duration']), iid=video['id'])
        
        ttk.Label(scene2, text="* Ctrl 또는 Shift 키를 사용하여 여러 영상을 선택할 수 있습니다.").pack(pady=5, anchor='w')

        button_frame = ttk.Frame(scene2)
        button_frame.pack(fill='x', pady=10)

        self.confirm_btn2 = ttk.Button(button_frame, text="선택한 영상 분석 시작", command=self.start_processing)
        self.confirm_btn2.pack(side="left", expand=True, fill="x", ipady=5, padx=(0, 5))

        self.load_more_btn = ttk.Button(button_frame, text="추가 로드", command=self.load_more_videos)
        self.load_more_btn.pack(side="right", expand=True, fill="x", ipady=5, padx=(5, 0))
        
        if len(self.all_videos) <= 30:
            self.load_more_btn.config(state="disabled")
            
        return scene2

    def load_more_videos(self):
        currently_loaded = len(self.tree.get_children())
        remaining_videos = self.all_videos[currently_loaded:]
        
        for video in remaining_videos:
            self.tree.insert("", "end", values=(video['title'], video['duration']), iid=video['id'])
            
        self.load_more_btn.config(state="disabled")

    def start_processing(self):
        selected_ids = self.tree.selection()
        if not selected_ids:
            messagebox.showerror("선택 오류", "하나 이상의 영상을 선택하세요.")
            return
        
        all_videos = youtube_helper.LAST_FETCHED_VIDEOS
        self.selected_videos = [v for v in all_videos if v['id'] in selected_ids]
        
        self.switch_scene(self.create_scene3)
        threading.Thread(target=self.process_videos_thread, daemon=True).start()

    def create_scene3(self):
        scene3 = ttk.Frame(self, padding=(20, 20))
        scene3.pack(fill="both", expand=True)
        
        ttk.Label(scene3, text="작업 진행 상황", font=("Helvetica", int(self.font_size*1.3), "bold")).pack(pady=10, anchor='w')
        self.progress_text = scrolledtext.ScrolledText(scene3, height=20, relief="solid", borderwidth=1, state="disabled")
        self.progress_text.pack(fill="both", expand=True)
        
        self.update_idletasks()
        return scene3

    def process_videos_thread(self):
        total = len(self.selected_videos)
        batch_size = CONFIG.get("gemini_batch_size", 30)
        
        video_map = {v['id']: v for v in self.selected_videos}

        for i in range(0, total, batch_size):
            batch_videos = self.selected_videos[i:i+batch_size]
            self.q.put(("log", f"--- 배치 처리 시작: {i+1} ~ {min(i+batch_size, total)} / {total} ---"))

            tasks = []
            for video in batch_videos:
                video_id = video['id']
                video_title = video['title']
                self.q.put(("log", f"  - '{video_title}' 스크립트 준비 중..."))
                try:
                    transcript, _ = youtube_helper.get_transcript(video_id)
                    if not transcript:
                        self.q.put(("log", f"  - 경고: '{video_title}' 스크립트를 찾을 수 없어 건너뜁니다."))
                        continue
                    
                    prompt_with_title = f"영상 제목: {video_title}\n\n{self.user_prompt}"
                    full_prompt = f"{prompt_with_title}\n\n--- 원본 스크립트 ---\n{transcript}\n--- 원본 스크립트 끝 ---"
                    tasks.append({"id": video_id, "task": full_prompt})

                except Exception as e:
                    self.q.put(("log", f"  - ✗ 오류: '{video_title}' 스크립트 추출 중 문제 발생 - {e}"))

            if not tasks:
                self.q.put(("log", "--- 현재 배치에서 처리할 작업이 없습니다. ---"))
                continue

            try:
                self.q.put(("log", f"  - Gemini API로 {len(tasks)}개 작업 배치 요청..."))
                results = gemini_helper.process_batch_with_gemini(tasks)
                
                result_map = {res['id']: res['result'] for res in results}

                for task in tasks:
                    video_id = task['id']
                    video_title = video_map[video_id]['title']
                    
                    if video_id in result_map:
                        processed_content = result_map[video_id]
                        self.q.put(("log", f"  - '{video_title}' 내용 가공 완료. 노트 저장 중..."))
                        file_helper.save_as_obsidian_note(self.obsidian_path, processed_content)
                        self.q.put(("log", f"  - ✓ 완료: '{video_title}' 노트 생성 완료"))
                    else:
                        self.q.put(("log", f"  - ✗ 오류: '{video_title}' 처리 결과가 없습니다."))

            except Exception as e:
                self.q.put(("log", f"  - ✗ 오류: Gemini 배치 처리 중 문제 발생 - {e}"))
        
        self.q.put(("done", "모든 작업이 완료되었습니다!"))

    def log_message(self, message):
        try:
            if hasattr(self, 'progress_text') and self.progress_text.winfo_exists():
                self.progress_text.config(state="normal")
                if isinstance(message, tuple) and message[0] == 'progress':
                    # 마지막 줄을 캐리지 리턴으로 덮어쓰기
                    self.progress_text.delete("end-1l", "end")
                    self.progress_text.insert(tk.END, f"  - Gemini 처리 진행도: {message[1]}%\r")
                else:
                    self.progress_text.insert(tk.END, message + "\n")
                self.progress_text.config(state="disabled")
                self.progress_text.see(tk.END)
        except Exception as e:
            print(f"로그 메시지 표시 오류: {e}")
            print(f"원본 메시지: {message}")

    def process_queue(self):
        try:
            msg_type, data = self.q.get_nowait()
            if msg_type == "videos_fetched":
                self.switch_scene(self.create_scene2, data)
            elif msg_type == "error":
                messagebox.showerror("오류", data)
                if hasattr(self, 'confirm_btn1'):
                    self.confirm_btn1.config(state="normal", text="영상 목록 불러오기")
            elif msg_type == "log":
                self.log_message(data)
            elif msg_type == "progress":
                self.log_message(("progress", data))
            elif msg_type == "done":
                self.log_message(f"\n--- {data} ---")
                messagebox.showinfo("완료", data)

        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_queue)

if __name__ == "__main__":
    try:
        if not youtube_helper.YOUTUBE_API_KEY:
            raise ValueError("YouTube API 키가 설정되지 않았습니다. MYAPI.json 파일을 확인해주세요.")
        if not gemini_helper.GEMINI_API_KEY:
            raise ValueError("Gemini API 키가 설정되지 않았습니다. MYAPI.json 파일을 확인해주세요.")
        
        # Gemini API 접근성 확인
        is_accessible, message = gemini_helper.check_gemini_api()
        if not is_accessible:
            # API 접근 불가 시, 사용자에게 알리고 프로그램 종료
            print(f"오류: {message}")
            messagebox.showerror("API 연결 오류", f"{message}\n\nIP가 차단되었거나 네트워크 연결에 문제가 있을 수 있습니다. 프로그램을 종료합니다.")
        else:
            print(message) # API 접근 가능 메시지 출력
            app = App()
            app.mainloop()

    except ValueError as e:
        print(f"오류: {e}")
        print("MYAPI.json 파일에 유효한 API 키를 설정해주세요.")
        messagebox.showerror("설정 오류", str(e))