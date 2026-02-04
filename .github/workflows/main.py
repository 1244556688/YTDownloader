import customtkinter as ctk
from tkinter import filedialog, messagebox, Listbox, Scrollbar
import subprocess
import threading
import os
import webbrowser

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

download_folder = ""
download_queue = []

def select_folder():
    global download_folder
    folder = filedialog.askdirectory()
    if folder:
        download_folder = folder
        folder_label.configure(text=f"下載資料夾: {download_folder}")

def add_to_queue():
    urls_text = url_text.get("1.0", ctk.END).strip()
    if not urls_text:
        messagebox.showerror("錯誤", "請輸入至少一個網址")
        return
    lines = [line.strip() for line in urls_text.splitlines() if line.strip()]
    for url in lines:
        download_queue.append(url)
        queue_list.insert(ctk.END, url)
    url_text.delete("1.0", ctk.END)

def remove_from_queue():
    selected = queue_list.curselection()
    for i in reversed(selected):
        download_queue.pop(i)
        queue_list.delete(i)

def download_queue_func():
    if not download_queue:
        messagebox.showerror("錯誤", "下載隊列為空")
        return
    if not download_folder:
        messagebox.showerror("錯誤", "請選擇下載資料夾")
        return

    mode = type_var.get()
    file_type = file_var.get()

    def download_worker():
        for url in download_queue:
            try:
                output_text.configure(state="normal")
                output_text.insert(ctk.END, f"開始下載: {url}\n")
                output_text.see(ctk.END)

                output_path = os.path.join(download_folder, "%(title)s.%(ext)s")
                cmd = ["yt-dlp", "-o", output_path, "--newline", url]

                if mode == "單支影片":
                    cmd.insert(1, "--no-playlist")

                if file_type == "MP4":
                    cmd.insert(1, "-f")
                    cmd.insert(2, "bestvideo+bestaudio")
                    cmd.insert(3, "--merge-output-format")
                    cmd.insert(4, "mp4")
                elif file_type == "MP3":
                    cmd.insert(1, "-x")
                    cmd.insert(2, "--audio-format")
                    cmd.insert(3, "mp3")

                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )

                for line in process.stdout:
                    output_text.insert(ctk.END, line)
                    output_text.see(ctk.END)
                    if "[download]" in line and "%" in line:
                        percent = line.split("%")[0].split()[-1]
                        try:
                            progress_bar.set(float(percent)/100)
                        except:
                            pass

                process.wait()
                output_text.insert(ctk.END, "下載完成！\n\n")
                progress_bar.set(0)
                output_text.see(ctk.END)
            except Exception as e:
                messagebox.showerror("錯誤", str(e))
        output_text.insert(ctk.END, "所有下載完成！\n")
        output_text.see(ctk.END)
        webbrowser.open(download_folder)
        output_text.configure(state="disabled")

    threading.Thread(target=download_worker).start()

# 主視窗
root = ctk.CTk()
root.title("專業 YT / 音樂下載器")
root.geometry("800x750")
root.resizable(False, False)

# URL 多行輸入
ctk.CTkLabel(root, text="輸入影片網址（每行一個）:", font=("Arial", 14)).pack(pady=5)
url_text = ctk.CTkTextbox(root, width=700, height=100, font=("Consolas", 12))
url_text.pack(pady=5)

# 添加/移除隊列按鈕
btn_frame = ctk.CTkFrame(root)
btn_frame.pack(pady=5)
ctk.CTkButton(btn_frame, text="加入隊列", command=add_to_queue, width=100).grid(row=0, column=0, padx=5)
ctk.CTkButton(btn_frame, text="移除隊列", command=remove_from_queue, width=100).grid(row=0, column=1, padx=5)

# 隊列顯示（使用 Tkinter Listbox）
list_frame = ctk.CTkFrame(root)
list_frame.pack(pady=5)

scrollbar = Scrollbar(list_frame)
scrollbar.pack(side="right", fill="y")

queue_list = Listbox(list_frame, width=95, height=6, font=("Consolas", 11), yscrollcommand=scrollbar.set, selectmode="extended")
queue_list.pack(side="left", fill="both")
scrollbar.config(command=queue_list.yview)

# 選資料夾
ctk.CTkButton(root, text="選擇下載資料夾", command=select_folder).pack(pady=5)
folder_label = ctk.CTkLabel(root, text="下載資料夾: 未選擇", font=("Arial", 12))
folder_label.pack(pady=5)

# 選單：單支 / 播放清單
ctk.CTkLabel(root, text="下載模式:", font=("Arial", 14)).pack(pady=5)
type_var = ctk.StringVar(value="單支影片")
ctk.CTkOptionMenu(root, variable=type_var, values=["單支影片", "整個播放清單"]).pack(pady=5)

# 選單：檔案格式
ctk.CTkLabel(root, text="檔案格式:", font=("Arial", 14)).pack(pady=5)
file_var = ctk.StringVar(value="MP4")
ctk.CTkOptionMenu(root, variable=file_var, values=["WebM", "MP4", "MP3"]).pack(pady=5)

# 下載按鈕
ctk.CTkButton(root, text="開始下載隊列", command=download_queue_func,
              fg_color="#1f6aa5", hover_color="#3b8ed0", font=("Arial", 14)).pack(pady=10)

# 進度條
progress_bar = ctk.CTkProgressBar(root, width=700)
progress_bar.pack(pady=5)
progress_bar.set(0)

# 文字區域
output_text = ctk.CTkTextbox(root, width=750, height=300, font=("Consolas", 11))
output_text.pack(pady=10)
output_text.configure(state="disabled")

root.mainloop()
