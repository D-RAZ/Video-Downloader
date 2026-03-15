import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import subprocess
import threading
import re
import os
import sys
import shutil
import json
import webbrowser


class YTDLPGui:

    def toggle_embed_checkbox(self):
        if self.caption_var.get():
            self.embed_checkbox.config(state="normal")
            self.embed_var.set(True)
        else:
            self.embed_checkbox.config(state="disabled")
            self.embed_var.set(False)

    def __init__(self, root):
        self.root = root
        self.root.title("Video Downloader")
        self.root.geometry("520x340")
        self.root.configure(bg="#121212")
        self.root.resizable(False, False)

        if getattr(sys, 'frozen', False):
            self.base_path = os.path.dirname(sys.executable)
            self.download_path = os.path.dirname(sys.executable)
        else:
            self.base_path = os.path.dirname(os.path.abspath(__file__))
            self.download_path = os.path.dirname(os.path.abspath(__file__))

        self.dependencies_path = os.path.join(self.base_path, "dependencies")
        self.settings_file = os.path.join(self.dependencies_path, "settings.json")

        self.create_widgets()
        self.load_settings()

        self.root.after(100, self.check_for_updates)

    # ---------------- SETTINGS ---------------- #

    def save_settings(self):
        try:
            data = {
                "quality": self.quality_var.get(),
                "download_path": self.download_path,
                "caption": self.caption_var.get(),
                "embed": self.embed_var.get()
            }

            with open(self.settings_file, "w") as f:
                json.dump(data, f, indent=4)

        except Exception:
            pass

    def load_settings(self):
        try:
            if not os.path.exists(self.settings_file):
                return

            with open(self.settings_file, "r") as f:
                data = json.load(f)

            quality = data.get("quality")
            if quality and quality in self.quality_dropdown["values"]:
                self.quality_var.set(quality)

            folder = data.get("download_path")
            if folder and os.path.isdir(folder):
                self.download_path = folder
                self.path_label.config(text=f"Folder: {folder}")

            self.caption_var.set(data.get("caption", False))
            self.embed_var.set(data.get("embed", False))

            self.toggle_embed_checkbox()

        except Exception:
            pass

    # ---------------- UPDATE CHECK ---------------- #

    def check_for_updates(self):
        pass

    # ---------------- FFMPEG ---------------- #

    def get_ffmpeg_path(self):

        local_ffmpeg = os.path.join(
            self.dependencies_path,
            "ffmpeg.exe" if sys.platform.startswith("win") else "ffmpeg"
        )

        if os.path.exists(local_ffmpeg):
            return local_ffmpeg

        return shutil.which("ffmpeg")

    # ---------------- UI ---------------- #

    def create_widgets(self):

        title = tk.Label(
            self.root,
            text="Video Downloader",
            bg="#121212",
            fg="white",
            font=("Segoe UI", 16, "bold")
        )
        title.pack(pady=10)

        self.url_entry = tk.Entry(
            self.root,
            width=60,
            bg="#1E1E1E",
            fg="white",
            insertbackground="white",
            relief="flat"
        )
        self.url_entry.pack(pady=5, ipady=6)

        self.placeholder_text = "Enter URL here"
        self.url_entry.insert(0, self.placeholder_text)
        self.url_entry.config(fg="grey")

        def on_focus_in(event):
            if self.url_entry.get() == self.placeholder_text:
                self.url_entry.delete(0, tk.END)
                self.url_entry.config(fg="white")

        def on_focus_out(event):
            if not self.url_entry.get():
                self.url_entry.insert(0, self.placeholder_text)
                self.url_entry.config(fg="grey")

        self.url_entry.bind("<FocusIn>", on_focus_in)
        self.url_entry.bind("<FocusOut>", on_focus_out)

        quality_frame = tk.Frame(self.root, bg="#121212")
        quality_frame.pack(pady=5)

        tk.Label(
            quality_frame,
            text="Select Quality:",
            bg="#121212",
            fg="white"
        ).pack(side=tk.LEFT, padx=5)

        self.quality_var = tk.StringVar()

        self.quality_dropdown = ttk.Combobox(
            quality_frame,
            textvariable=self.quality_var,
            state="readonly",
            width=18
        )

        self.quality_dropdown["values"] = (
            "Best",
            "1080p",
            "720p",
            "480p",
            "Audio Only (MP3)"
        )

        self.quality_dropdown.current(0)
        self.quality_dropdown.pack(side=tk.LEFT)

        caption_frame = tk.Frame(self.root, bg="#121212")
        caption_frame.pack(pady=3, anchor="w")

        self.caption_var = tk.BooleanVar()
        self.embed_var = tk.BooleanVar()

        self.caption_checkbox = tk.Checkbutton(
            caption_frame,
            text="Include caption",
            variable=self.caption_var,
            command=self.toggle_embed_checkbox,
            bg="#121212",
            fg="white",
            selectcolor="#121212",
            activebackground="#121212",
            activeforeground="white"
        )
        self.caption_checkbox.pack(anchor="w")

        self.embed_checkbox = tk.Checkbutton(
            caption_frame,
            text="Embed",
            variable=self.embed_var,
            bg="#121212",
            fg="white",
            selectcolor="#121212",
            activebackground="#121212",
            activeforeground="white"
        )
        self.embed_checkbox.pack(anchor="w", padx=25)

        self.toggle_embed_checkbox()

        path_frame = tk.Frame(self.root, bg="#121212")
        path_frame.pack(pady=5)

        self.path_label = tk.Label(
            path_frame,
            text=f"Folder: {self.download_path}",
            bg="#121212",
            fg="#BBBBBB"
        )
        self.path_label.pack(side=tk.LEFT)

        self.browse_btn = tk.Button(
            path_frame,
            text="Browse",
            command=self.select_folder,
            bg="#2A2A2A",
            fg="white",
            relief="flat"
        )
        self.browse_btn.pack(side=tk.LEFT, padx=10)

        self.progress = ttk.Progressbar(
            self.root,
            orient="horizontal",
            length=450,
            mode="determinate"
        )
        self.progress.pack(pady=15)

        self.status_label = tk.Label(
            self.root,
            text="Status: Waiting",
            bg="#121212",
            fg="#BBBBBB",
            font=("Segoe UI", 10)
        )
        self.status_label.pack(pady=5)

        self.download_btn = tk.Button(
            self.root,
            text="Download",
            command=self.start_download,
            bg="#00C853",
            fg="black",
            font=("Segoe UI", 10, "bold"),
            relief="flat"
        )
        self.download_btn.pack(pady=5)

        credit_frame = tk.Frame(self.root, bg="#121212")
        credit_frame.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-8)

        tk.Label(
            credit_frame,
            text="Developed by ",
            bg="#121212",
            fg="#888888",
            font=("Segoe UI", 8)
        ).pack(side="left")

        link = tk.Label(
            credit_frame,
            text="d-raz",
            bg="#121212",
            fg="#4FC3F7",
            cursor="hand2",
            font=("Segoe UI", 8, "underline")
        )
        link.pack(side="left")

        link.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/d-raz"))

    # ---------------- Utility ---------------- #

    def set_widgets_state(self, state):

        self.url_entry.config(state=state)

        self.quality_dropdown.config(
            state="readonly" if state == "normal" else "disabled"
        )

        self.browse_btn.config(state=state)
        self.download_btn.config(state=state)
        self.caption_checkbox.config(state=state)

        if state == "normal" and self.caption_var.get():
            self.embed_checkbox.config(state="normal")
        else:
            self.embed_checkbox.config(state="disabled")

    # ---------------- Folder Selection ---------------- #

    def select_folder(self):

        folder = filedialog.askdirectory()

        if folder:
            self.download_path = folder
            self.path_label.config(text=f"Folder: {folder}")

    # ---------------- Start Download ---------------- #

    def start_download(self):

        url = self.url_entry.get().strip()

        if url == self.placeholder_text or not url:
            messagebox.showerror("Error", "Please enter a URL")
            return

        if "Audio Only" not in self.quality_var.get():
            if not self.check_ffmpeg():
                return

        self.save_settings()

        self.progress["value"] = 0

        self.status_label.config(text="Status: Analysing URL...", fg="#00C853")

        self.set_widgets_state("disabled")

        threading.Thread(
            target=self.analyse_and_download,
            args=(url,),
            daemon=True
        ).start()

    # ---------------- Caption Analysis ---------------- #

    def analyse_and_download(self, url):

        if not self.caption_var.get():
            self.root.after(
                0,
                lambda: self.status_label.config(text="Status: Downloading...", fg="#00C853")
            )
            self.download_video(url)
            return

        yt_dlp_executable = self.get_yt_dlp_path()

        try:

            command = [
                yt_dlp_executable,
                "--dump-json",
                "--skip-download",
                url
            ]

            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if not result.stdout.strip():
                raise Exception("Unable to analyse video")

            info = json.loads(result.stdout)

            captions_available = False

            if info.get("subtitles") or info.get("automatic_captions"):
                captions_available = True

            if captions_available:

                self.root.after(
                    0,
                    lambda: self.status_label.config(text="Status: Downloading...", fg="#00C853")
                )

                self.download_video(url)

            else:

                self.root.after(
                    0,
                    lambda: self.show_caption_missing_dialog(url)
                )

        except Exception:

            self.root.after(
                0,
                lambda: self.show_caption_missing_dialog(url)
            )

    # ---------------- Caption Missing Dialog ---------------- #

    def show_caption_missing_dialog(self, url):

        dialog = tk.Toplevel(self.root)
        dialog.title("Caption Not Available")
        dialog.geometry("360x140")
        dialog.configure(bg="#121212")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.attributes("-topmost", True)

        tk.Label(
            dialog,
            text="Caption for the video is not available.",
            bg="#121212",
            fg="white",
            font=("Segoe UI", 10)
        ).pack(pady=20)

        btn_frame = tk.Frame(dialog, bg="#121212")
        btn_frame.pack(pady=10)

        def proceed():
            dialog.destroy()

            self.caption_var.set(False)
            self.embed_var.set(False)

            self.root.after(
                0,
                lambda: self.status_label.config(text="Status: Downloading...", fg="#00C853")
            )

            threading.Thread(
                target=self.download_video,
                args=(url,),
                daemon=True
            ).start()

        def cancel():
            dialog.destroy()
            self.progress["value"] = 0
            self.enable_ui()

        tk.Button(
            btn_frame,
            text="Proceed",
            bg="#00C853",
            fg="black",
            width=12,
            command=proceed,
            relief="flat"
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            btn_frame,
            text="Cancel Download",
            bg="#2A2A2A",
            fg="white",
            width=14,
            command=cancel,
            relief="flat"
        ).pack(side=tk.LEFT, padx=10)

    # ---------------- FFmpeg Detection ---------------- #

    def check_ffmpeg(self):

        ffmpeg_path = self.get_ffmpeg_path()

        if not ffmpeg_path:
            self.root.after(
                0,
                lambda: messagebox.showerror(
                    "FFmpeg Not Found",
                    "FFmpeg is required but was not found."
                )
            )
            return False

        return True

    # ---------------- yt-dlp Path ---------------- #

    def get_yt_dlp_path(self):

        local_exe = os.path.join(
            self.dependencies_path,
            "yt-dlp.exe" if sys.platform.startswith("win") else "yt-dlp"
        )

        return local_exe if os.path.exists(local_exe) else "yt-dlp"

    # ---------------- Format ---------------- #

    def get_format_string(self):

        quality = self.quality_var.get()

        if quality == "Best":
            return "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]"

        elif quality == "1080p":
            return "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]"

        elif quality == "720p":
            return "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]"

        elif quality == "480p":
            return "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]"

        elif quality == "Audio Only (MP3)":
            return "bestaudio"

        return "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]"

    # ---------------- Download ---------------- #

    def download_video(self, url):

        try:

            output_template = os.path.join(
                self.download_path,
                "%(title)s.mp4"
            ) if "Audio Only" not in self.quality_var.get() else os.path.join(
                self.download_path,
                "%(title)s.%(ext)s"
            )

            format_string = self.get_format_string()
            yt_dlp_executable = self.get_yt_dlp_path()
            ffmpeg_path = self.get_ffmpeg_path()

            command = [
                yt_dlp_executable,
                "--no-config",
                "-f",
                format_string,
                "-o",
                output_template
            ]

            if ffmpeg_path:
                command.extend(["--ffmpeg-location", ffmpeg_path])

            if self.caption_var.get():
                command.extend([
                    "--write-subs",
                    "--write-auto-subs",
                    "--sub-langs", "en"
                ])

                if self.embed_var.get():
                    command.append("--embed-subs")

            if "Audio Only" not in self.quality_var.get():
                command.extend(["--merge-output-format", "mp4"])

            if "Audio Only" in self.quality_var.get():
                command.extend(["--extract-audio", "--audio-format", "mp3"])

            command.append(url)

            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            for line in process.stdout:

                if "%" in line:

                    match = re.search(r'(\d+(?:\.\d+)?)%', line)

                    if match:
                        percent = float(match.group(1))

                        self.root.after(
                            0,
                            self.progress.config,
                            {"value": percent}
                        )

            process.wait()

            if process.returncode == 0:

                if self.caption_var.get() and self.embed_var.get():
                    for file in os.listdir(self.download_path):
                        if file.endswith((".vtt", ".srt")):
                            file_path = os.path.join(self.download_path, file)
                            try:
                                os.remove(file_path)
                            except Exception:
                                pass

                self.root.after(
                    0,
                    lambda: self.show_completion_dialog()
                )
                self.root.after(
                    0,
                    lambda: self.status_label.config(text="Status: Completed", fg="#00C853")
                )

            else:

                self.root.after(
                    0,
                    lambda: messagebox.showerror(
                        "Download Failed",
                        "Unknown error occurred."
                    )
                )

                self.root.after(0, self.enable_ui)

        except Exception as e:

            self.root.after(
                0,
                lambda: messagebox.showerror(
                    "Error",
                    str(e)
                )
            )

            self.root.after(0, self.enable_ui)


    # ---------------- Completion Dialog ---------------- #

    def show_completion_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Download Completed")
        dialog.geometry("350x120")
        dialog.configure(bg="#121212")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.attributes("-topmost", True)

        tk.Label(
            dialog,
            text="Download completed successfully!",
            bg="#121212",
            fg="white",
            font=("Segoe UI", 11, "bold")
        ).pack(pady=15)

        btn_frame = tk.Frame(dialog, bg="#121212")
        btn_frame.pack(pady=10)

        def open_folder():
            if sys.platform.startswith("win"):
                os.startfile(self.download_path)
            else:
                subprocess.run(["xdg-open", self.download_path])
            dialog.destroy()
            self.enable_ui()
            self.progress["value"] = 0

        def close_dialog():
            dialog.destroy()
            self.enable_ui()
            self.progress["value"] = 0

        tk.Button(
            btn_frame,
            text="Open Folder",
            bg="#00C853",
            fg="black",
            width=12,
            command=open_folder,
            relief="flat"
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            btn_frame,
            text="OK",
            bg="#2A2A2A",
            fg="white",
            width=12,
            command=close_dialog,
            relief="flat"
        ).pack(side=tk.LEFT, padx=10)

    # ---------------- Enable UI ---------------- #

    def enable_ui(self):

        self.set_widgets_state("normal")

        self.status_label.config(
            text="Status: Waiting",
            fg="#BBBBBB"
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = YTDLPGui(root)
    root.mainloop()