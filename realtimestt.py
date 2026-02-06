from RealtimeSTT import AudioToTextRecorder
import pystray
from PIL import Image, ImageDraw, ImageFont
import keyboard
import pyautogui
import pyperclip
import threading
import time

LANGUAGES = [
    ("ko", "한국어", "KR"),
    ("en", "English", "EN"),
    ("ja", "日本語", "JP"),
    ("zh", "中文", "CH"),
    ("vi", "Tiếng Việt", "VN"),
]

ICON_SIZE = 256
FONT_SIZE = 140
COLOR_REC = (255, 50, 50)
COLOR_IDLE = (0, 122, 255)


class VoiceRecorderApp:
    def __init__(self):
        self._lock = threading.Lock()
        self.is_recording = False
        self.is_transcribing = False
        self.lang_idx = 0

        self.recorder = AudioToTextRecorder(
            model="large-v3-turbo",
            language="ko",
            spinner=False,
            no_log_file=True,
        )

        self._font = self._load_font()
        self.icon = pystray.Icon("voice_recorder")
        self._update_icon()

        keyboard.add_hotkey("ctrl+shift+space", self.toggle_recording)
        keyboard.add_hotkey("alt+shift+l", self.cycle_language)

    @property
    def lang(self):
        return LANGUAGES[self.lang_idx]

    @staticmethod
    def _load_font():
        for name in ("arialbd.ttf", "arial.ttf", "DejaVuSans-Bold.ttf"):
            try:
                return ImageFont.truetype(name, FONT_SIZE)
            except (IOError, OSError):
                continue
        return ImageFont.load_default()

    def _create_image(self):
        img = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        bg = COLOR_REC if self.is_recording else COLOR_IDLE
        draw.rectangle([0, 0, ICON_SIZE, ICON_SIZE], fill=bg)

        badge = self.lang[2]
        bbox = draw.textbbox((0, 0), badge, font=self._font)
        x = (ICON_SIZE - bbox[2] + bbox[0]) // 2
        y = (ICON_SIZE - bbox[3] + bbox[1]) // 2 - 10
        draw.text((x, y), badge, fill="white", font=self._font)
        return img

    def _build_menu(self):
        lang_items = [
            pystray.MenuItem(
                f"{'✓ ' if i == self.lang_idx else '   '}{name}",
                lambda _, c=code: self.set_language(c),
            )
            for i, (code, name, _) in enumerate(LANGUAGES)
        ]

        if self.is_transcribing:
            toggle_label = "⏳ 변환 중..."
        elif self.is_recording:
            toggle_label = "🔴 녹음 중지"
        else:
            toggle_label = "🎤 녹음 시작"

        return pystray.Menu(
            pystray.MenuItem(
                toggle_label,
                lambda _, __: self.toggle_recording(),
                enabled=not self.is_transcribing,
            ),
            pystray.MenuItem("단축키: Ctrl+Shift+Space", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("언어 (Alt+Shift+L)", pystray.Menu(*lang_items)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("종료", lambda _, __: self.quit()),
        )

    def _update_icon(self):
        prefix = "[녹음중] " if self.is_recording else ""
        self.icon.icon = self._create_image()
        self.icon.title = f"{prefix}음성 인식 - {self.lang[1]}"
        self.icon.menu = self._build_menu()

    def toggle_recording(self):
        with self._lock:
            if self.is_transcribing:
                return
            if self.is_recording:
                self._stop_recording()
            else:
                self._start_recording()

    def _start_recording(self):
        self.is_recording = True
        self._update_icon()
        self.recorder.start()

    def _stop_recording(self):
        self.is_recording = False
        self.is_transcribing = True
        self._update_icon()

        def transcribe():
            self.recorder.stop()
            text = self.recorder.text().strip()
            if text:
                pyperclip.copy(text)
                time.sleep(0.1)
                pyautogui.hotkey("ctrl", "v")
            with self._lock:
                self.is_transcribing = False
                self._update_icon()

        threading.Thread(target=transcribe, daemon=True).start()

    def set_language(self, code):
        with self._lock:
            self.lang_idx = next(
                i for i, (c, *_) in enumerate(LANGUAGES) if c == code
            )
            self.recorder.language = code
            self._update_icon()

    def cycle_language(self):
        with self._lock:
            self.lang_idx = (self.lang_idx + 1) % len(LANGUAGES)
            self.recorder.language = self.lang[0]
            self._update_icon()

    def quit(self):
        if self.is_recording:
            self.recorder.stop()
        keyboard.unhook_all()
        self.recorder.shutdown()
        self.icon.stop()

    def run(self):
        self.icon.run()


if __name__ == "__main__":
    app = VoiceRecorderApp()
    app.run()
