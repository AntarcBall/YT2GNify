# main.py
# tkinter를 사용하여 GUI 애플리케이션을 생성하고 전체 프로세스를 제어합니다.

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import queue
import json
import os
from utils import youtube_helper, gemini_helper, file_helper

def load_prompt_from_json(filepath="default_prompt.json"):
    """JSON 파일에서 기본 프롬프트를 로드합니다."""
    # 스크립트가 있는 디렉토리에서 JSON 파일 찾기
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

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube 스크립트 분석기")
        self.geometry("1024x768")

        # --- UI 상태 변수 ---
        self.font_size = 12
        self.is_dark_mode = tk.BooleanVar(value=True)  # 기본 다크 모드
        
        # --- 스타일 설정 ---
        self.style = ttk.Style(self)
        self.update_styles()

        self.q = queue.Queue()
        self.after(100, self.process_queue)

        self.current_scene = None
        self.current_scene = self.create_scene1()

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
        self.style.configure('Treeview', background=tree_bg, fieldbackground=tree_bg, foreground=fg_color)
        self.style.configure('Treeview.Heading', background=tree_heading_bg, foreground=fg_color, font=heading_font)
        self.style.map('Treeview.Heading', background=[('active', '#6E6E6E' if self.is_dark_mode.get() else '#D0D0D0')])

        # Only configure widgets if they exist and are valid
        if hasattr(self, 'prompt_text') and self.prompt_text.winfo_exists():
            try:
                self.prompt_text.config(bg=entry_bg, fg=fg_color, insertbackground=fg_color, font=current_font)
            except tk.TclError:
                pass  # Widget may have been destroyed
        
        if hasattr(self, 'progress_text') and self.progress_text.winfo_exists():
            try:
                self.progress_text.config(bg=entry_bg, fg=fg_color, font=current_font)
            except tk.TclError:
                pass  # Widget may have been destroyed
            
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

        main_content_frame = ttk.Frame(scene1)
        main_content_frame.pack(fill="both", expand=True)

        ttk.Label(main_content_frame, text="유튜브 채널 URL:").pack(pady=(0, 5), anchor='w')
        self.url_entry = ttk.Entry(main_content_frame)
        self.url_entry.pack(fill="x", pady=(0, 15))
        self.url_entry.insert(0, "https://www.youtube.com/@slow_doctor")

        ttk.Label(main_content_frame, text="Obsidian 저장 경로:").pack(pady=(0, 5), anchor='w')
        path_frame = ttk.Frame(main_content_frame)
        path_frame.pack(fill="x", pady=(0, 15))
        self.path_entry = ttk.Entry(path_frame)
        self.path_entry.pack(side="left", fill="x", expand=True)
        self.path_entry.insert(0, 'C:/Users/bounc/문서/SummerVCT/Notes')
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

        if not self.channel_url or not self.obsidian_path:
            messagebox.showerror("입력 오류", "채널 URL과 저장 경로는 필수입니다.")
            return

        self.confirm_btn1.config(state="disabled", text="불러오는 중...")
        threading.Thread(target=self.fetch_videos_thread, daemon=True).start()

    def fetch_videos_thread(self):
        try:
            videos = youtube_helper.get_videos_from_channel(self.channel_url)
            self.q.put(("videos_fetched", videos))
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

        self.confirm_btn2 = ttk.Button(scene2, text="선택한 영상 분석 시작", command=self.start_processing)
        self.confirm_btn2.pack(pady=10, ipady=5)
        
        return scene2

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
        for i, video in enumerate(self.selected_videos):
            video_id = video['id']
            video_title = video['title']
            self.q.put(("log", f"[{i+1}/{total}] '{video_title}' 영상 처리 시작..."))
            try:
                self.q.put(("log", "  - 스크립트 추출 중..."))
                transcript = youtube_helper.get_transcript(video_id)
                if not transcript:
                    self.q.put(("log", f"  - 경고: 스크립트를 찾을 수 없어 건너뜁니다."))
                    continue

                self.q.put(("log", "  - Gemini API로 내용 가공 중..."))
                prompt_with_title = f"영상 제목: {video_title}\n\n{self.user_prompt}"
                processed_content = gemini_helper.process_text_with_gemini(transcript, prompt_with_title)

                self.q.put(("log", "  - Obsidian 노트 저장 중..."))
                file_helper.save_as_obsidian_note(self.obsidian_path, processed_content)
                self.q.put(("log", f"  - ✓ 완료: '{video_title}' 노트 생성 완료\n"))

            except Exception as e:
                self.q.put(("log", f"  - ✗ 오류: 처리 중 문제 발생 - {e}\n"))
        
        self.q.put(("done", "모든 작업이 완료되었습니다!"))

    def log_message(self, message):
        try:
            if hasattr(self, 'progress_text') and self.progress_text.winfo_exists():
                self.progress_text.config(state="normal")
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
        app = App()
        app.mainloop()
    except ValueError as e:
        print(f"오류: {e}")
        print("MYAPI.json 파일에 유효한 API 키를 설정해주세요.")