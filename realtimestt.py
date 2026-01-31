from RealtimeSTT import AudioToTextRecorder
import tkinter as tk
import keyboard
import pyautogui

class VoiceRecorderApp:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("음성 인식")
        self.window.geometry("380x250")
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.text_label = tk.Label(self.window, text="버튼 또는 Ctrl+Shift+Space 누르고 말하세요", font=("Arial", 12))
        self.text_label.pack(pady=20)
        
        self.result_label = tk.Label(self.window, text="", font=("Arial", 14), wraplength=350)
        self.result_label.pack(pady=20)
        
        self.record_btn = tk.Button(self.window, text="🎤 누르고 말하기", font=("Arial", 14), width=16, height=1)
        self.record_btn.pack(pady=10)
        
        lang_frame = tk.Frame(self.window)
        lang_frame.pack(pady=10)

        self.lang = "ko"

        self.ko_btn = tk.Button(lang_frame, text="한국어", font=("Arial", 11), width=10, bg="#007aff", fg="white", relief="flat")
        self.en_btn = tk.Button(lang_frame, text="English", font=("Arial", 11), width=10, bg="gray", fg="white", relief="flat")

        self.ko_btn.pack(side="left", padx=5)
        self.en_btn.pack(side="left", padx=5)

        self.ko_btn.config(command=lambda: self.set_language("ko"))
        self.en_btn.config(command=lambda: self.set_language("en"))

        self.record_btn.bind("<ButtonPress>", self.start_recording)
        self.record_btn.bind("<ButtonRelease>", self.stop_recording)
        
        keyboard.on_press_key("space", self.on_hotkey_press, suppress=False)
        keyboard.on_release_key("space", self.on_hotkey_release, suppress=False)
        
        self.is_recording = False
        
        self.recorder = AudioToTextRecorder(
            model="large-v3-turbo",
            language="ko",
            enable_realtime_transcription=True,
            realtime_model_type="tiny",
            on_realtime_transcription_update=self.realtime_update,
        )
    def on_close(self):
        keyboard.unhook_all()
        self.recorder.shutdown()
        self.window.destroy()

    def set_language(self, lang):
        self.lang = lang
        self.recorder.language = lang
        
        if lang == "ko":
            self.ko_btn.config(bg="#007aff")
            self.en_btn.config(bg="gray")
        else:
            self.ko_btn.config(bg="gray")
            self.en_btn.config(bg="#007aff")

    def on_hotkey_press(self, event):
        if keyboard.is_pressed("ctrl") and keyboard.is_pressed("shift") and not self.is_recording:
            self.is_recording = True
            self.window.after(0, lambda: self.start_recording(None))
    
    def on_hotkey_release(self, event):
        if self.is_recording:
            self.is_recording = False
            self.window.after(0, lambda: self.stop_recording(None))
        
    def realtime_update(self, text):
        self.window.after(0, lambda: self.result_label.config(text=f"[실시간] {text}"))
        
    def start_recording(self, event):
        self.record_btn.config(bg="red", text="🔴 녹음 중...")
        self.recorder.start()
        
    def stop_recording(self, event):
        self.record_btn.config(bg="SystemButtonFace", text="🎤 누르고 말하기")
        self.recorder.stop()
        text = self.recorder.text()
        self.result_label.config(text=f"[최종] {text}")
        
        self.window.clipboard_clear()
        self.window.clipboard_append(text)
        
        self.window.after(100, lambda: pyautogui.hotkey("ctrl", "v"))
        
        self.text_label.config(text="✓ 붙여넣기 완료!")
        self.window.after(2000, lambda: self.text_label.config(text="버튼 또는 Ctrl+Shift+Space 누르고 말하세요"))
        
    def run(self):
        self.window.mainloop()

if __name__ == '__main__':
    app = VoiceRecorderApp()
    app.run()
