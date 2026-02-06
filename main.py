from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.utils import platform
from kivy.factory import Factory

import subprocess, threading, os, webbrowser

# ========= 全域設定 =========
FONT = "fonts/貌艙醳醳极楛-棉极.otf"

if platform == "android":
    DOWNLOAD_FOLDER = "/storage/emulated/0/Download"
else:
    DOWNLOAD_FOLDER = os.getcwd()

download_queue = []

# Spinner 下拉選單套字型（關鍵）
Factory.register('SpinnerOption', cls=Button)

# ========= UI =========
class DownloaderLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", spacing=10, padding=12, **kwargs)

        self.url_input = TextInput(
            hint_text="輸入影片網址（每行一個）",
            multiline=True,
            size_hint_y=None,
            height=150,
            font_name=FONT
        )
        self.add_widget(self.url_input)

        btns = BoxLayout(size_hint_y=None, height=45, spacing=10)
        self.add_btn = Button(text="加入隊列", font_name=FONT)
        self.remove_btn = Button(text="移除最後一個", font_name=FONT)
        btns.add_widget(self.add_btn)
        btns.add_widget(self.remove_btn)
        self.add_widget(btns)

        self.scroll = ScrollView(size_hint=(1, 0.25))
        self.queue_layout = GridLayout(cols=1, size_hint_y=None, spacing=5)
        self.queue_layout.bind(minimum_height=self.queue_layout.setter("height"))
        self.scroll.add_widget(self.queue_layout)
        self.add_widget(self.scroll)

        self.add_widget(Label(text="下載模式", font_name=FONT, size_hint_y=None, height=25))
        self.mode_spinner = Spinner(
            text="單支影片",
            values=["單支影片", "整個播放清單"],
            size_hint_y=None,
            height=40,
            font_name=FONT
        )
        self.add_widget(self.mode_spinner)

        self.add_widget(Label(text="檔案格式", font_name=FONT, size_hint_y=None, height=25))
        self.format_spinner = Spinner(
            text="MP4",
            values=["WebM", "MP4", "MP3"],
            size_hint_y=None,
            height=40,
            font_name=FONT
        )
        self.add_widget(self.format_spinner)

        self.download_btn = Button(
            text="開始下載隊列",
            size_hint_y=None,
            height=60,
            font_name=FONT
        )
        self.add_widget(self.download_btn)

        self.progress = ProgressBar(max=1, value=0)
        self.add_widget(self.progress)

        info = BoxLayout(size_hint_y=None, height=30)
        self.speed_label = Label(text="速度: --", font_name=FONT)
        self.eta_label = Label(text="剩餘: --", font_name=FONT)
        info.add_widget(self.speed_label)
        info.add_widget(self.eta_label)
        self.add_widget(info)

        self.output = TextInput(
            readonly=True,
            size_hint_y=0.35,
            font_name=FONT
        )
        self.add_widget(self.output)

        # 綁定
        self.add_btn.bind(on_release=self.add_to_queue)
        self.remove_btn.bind(on_release=self.remove_from_queue)
        self.download_btn.bind(on_release=self.start_download)

    # ========= 功能 =========
    def add_to_queue(self, _):
        lines = [l.strip() for l in self.url_input.text.splitlines() if l.strip()]
        for url in lines:
            download_queue.append(url)
            self.queue_layout.add_widget(
                Label(text=url, size_hint_y=None, height=28, font_name=FONT)
            )
        self.url_input.text = ""

    def remove_from_queue(self, _):
        if download_queue and self.queue_layout.children:
            download_queue.pop(-1)
            self.queue_layout.remove_widget(self.queue_layout.children[-1])

    def start_download(self, _):
        if not download_queue:
            self.output.text += "下載隊列為空\n"
            return

        mode = self.mode_spinner.text
        fmt = self.format_spinner.text

        def worker():
            for url in download_queue:
                self.log(f"開始下載: {url}")

                out = os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s")
                cmd = ["yt-dlp", "-o", out, "--newline", url]

                if mode == "單支影片":
                    cmd.insert(1, "--no-playlist")

                if fmt == "MP4":
                    cmd[1:1] = ["-f", "bestvideo+bestaudio", "--merge-output-format", "mp4"]
                elif fmt == "MP3":
                    cmd[1:1] = ["-x", "--audio-format", "mp3"]

                p = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )

                for line in p.stdout:
                    self.log(line, raw=True)
                    if "[download]" in line and "%" in line:
                        try:
                            parts = line.split()
                            percent = float(parts[1].replace("%", "")) / 100
                            speed = parts[6]
                            eta = parts[8]
                            Clock.schedule_once(lambda dt, v=percent: setattr(self.progress, "value", v))
                            Clock.schedule_once(lambda dt, s=speed: setattr(self.speed_label, "text", f"速度: {s}"))
                            Clock.schedule_once(lambda dt, e=eta: setattr(self.eta_label, "text", f"剩餘: {e}"))
                        except:
                            pass

                p.wait()
                self.log("下載完成！\n")
                Clock.schedule_once(lambda dt: setattr(self.progress, "value", 0))

            self.log("所有下載完成！")
            if platform != "android":
                webbrowser.open(DOWNLOAD_FOLDER)

        threading.Thread(target=worker, daemon=True).start()

    def log(self, text, raw=False):
        self.output.text += text if raw else text + "\n"
        self.output.cursor = (len(self.output.text), 0)


class YTDownloaderApp(App):
    def build(self):
        self.title = "YT Downloader"
        return DownloaderLayout()


if __name__ == "__main__":
    YTDownloaderApp().run()
