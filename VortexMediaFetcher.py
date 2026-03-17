import customtkinter as ctk
from tkinter import messagebox, filedialog
import tkinter as tk
import yt_dlp
from yt_dlp.networking.impersonate import ImpersonateTarget
import threading
import os
import sys
import re
import shutil
import traceback

# --- Resource Path Helper for PyInstaller ---
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- Modern UI Setup ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Vortex Media Fetcher")
app.geometry("600x500")
app.resizable(False, False)

# Set the custom window and taskbar icon
try:
    app.iconbitmap(resource_path("vortex.ico"))
except Exception:
    pass # If the icon is missing, it will just use the default Windows icon

# Global variable for the save directory
save_directory = os.getcwd()

# --- Core Functions ---
def browse_folder():
    global save_directory
    folder = filedialog.askdirectory(initialdir=save_directory)
    if folder:
        save_directory = folder
        folder_label.configure(text=f"Saving to: {save_directory}")

def paste_from_clipboard():
    try:
        clip_text = app.clipboard_get()
        url_entry.delete(0, tk.END)
        url_entry.insert(0, clip_text)
    except tk.TclError:
        messagebox.showinfo("Clipboard Empty", "There is no text in your clipboard to paste.")

def progress_hook(d):
    if d['status'] == 'downloading':
        try:
            percent_str = re.sub(r'\x1b\[[0-9;]*m', '', d['_percent_str']).strip().replace('%', '')
            percent = float(percent_str) / 100.0
            app.after(0, lambda: progress_bar.set(percent))
            app.after(0, lambda: status_label.configure(text=f"Downloading... {percent_str}%", text_color="cyan"))
        except Exception:
            pass
    elif d['status'] == 'finished':
        app.after(0, lambda: progress_bar.set(1.0))
        app.after(0, lambda: status_label.configure(text="Processing media... Please wait.", text_color="yellow"))

def process_download(url, format_choice, quality_choice, save_path):
    ydl_opts = {
        'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
        'noplaylist': True,
        'progress_hooks': [progress_hook],
        'quiet': False, 
        'nocheckcertificate': True,
        'impersonate': ImpersonateTarget(client='chrome') 
    }

    if format_choice == "MP3 (Audio Only)":
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    else: 
        if "tiktok.com" in url.lower():
            ydl_opts['format'] = 'b[ext=mp4]/b'
        else:
            if quality_choice == "Best Available":
                ydl_opts['format'] = 'bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best'
            elif quality_choice == "1080p":
                ydl_opts['format'] = 'bestvideo[height<=1080][ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best'
            elif quality_choice == "720p":
                ydl_opts['format'] = 'bestvideo[height<=720][ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best'
            elif quality_choice == "480p":
                ydl_opts['format'] = 'bestvideo[height<=480][ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best'
            ydl_opts['merge_output_format'] = 'mp4'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        app.after(0, lambda: status_label.configure(text="Download Complete!", text_color="green"))
    except Exception as e:
        error_message = repr(e)
        app.after(0, lambda: status_label.configure(text="Download Failed.", text_color="red"))
        app.after(0, lambda msg=error_message: messagebox.showerror("Error", f"An error occurred:\n{msg}"))
        print("\n--- DETAILED ERROR LOG ---")
        traceback.print_exc()
        print("--------------------------\n")
    finally:
        app.after(0, lambda: download_btn.configure(state="normal"))
        app.after(5000, lambda: progress_bar.set(0)) 

def start_download():
    if not shutil.which("ffmpeg"):
        messagebox.showerror(
            "FFmpeg Missing", 
            "Python cannot find FFmpeg! If you just installed it, you MUST completely close and restart your computer or terminal for the changes to take effect."
        )
        return

    url = url_entry.get()
    if not url:
        messagebox.showwarning("Input Error", "Please paste a valid media URL.")
        return

    format_choice = format_var.get()
    quality_choice = quality_var.get()

    download_btn.configure(state="disabled")
    status_label.configure(text="Initializing download...", text_color="white")
    progress_bar.set(0)

    threading.Thread(
        target=process_download, 
        args=(url, format_choice, quality_choice, save_directory), 
        daemon=True
    ).start()

# --- Building the UI Elements ---

title_label = ctk.CTkLabel(app, text="Vortex Media Fetcher", font=ctk.CTkFont(size=24, weight="bold"))
title_label.pack(pady=(25, 10))

url_frame = ctk.CTkFrame(app, fg_color="transparent")
url_frame.pack(pady=10)

url_entry = ctk.CTkEntry(url_frame, width=370, placeholder_text="Paste URL (YouTube, TikTok, Instagram...)")
url_entry.pack(side="left", padx=(0, 10))

paste_btn = ctk.CTkButton(url_frame, text="Paste", command=paste_from_clipboard, width=70, fg_color="#444444", hover_color="#555555")
paste_btn.pack(side="left")

options_frame = ctk.CTkFrame(app, fg_color="transparent")
options_frame.pack(pady=10)

format_var = ctk.StringVar(value="MP4 (Video)")
format_label = ctk.CTkLabel(options_frame, text="Format:")
format_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
format_menu = ctk.CTkOptionMenu(options_frame, variable=format_var, values=["MP4 (Video)", "MP3 (Audio Only)"])
format_menu.grid(row=1, column=0, padx=10)

quality_var = ctk.StringVar(value="Best Available")
quality_label = ctk.CTkLabel(options_frame, text="Video Quality:")
quality_label.grid(row=0, column=1, padx=10, pady=5, sticky="w")
quality_menu = ctk.CTkOptionMenu(options_frame, variable=quality_var, values=["Best Available", "1080p", "720p", "480p"])
quality_menu.grid(row=1, column=1, padx=10)

folder_frame = ctk.CTkFrame(app, fg_color="transparent")
folder_frame.pack(pady=(20, 5))

folder_btn = ctk.CTkButton(folder_frame, text="Choose Save Folder", command=browse_folder, width=150, fg_color="#444444", hover_color="#555555")
folder_btn.pack(side="left", padx=10)

folder_label = ctk.CTkLabel(folder_frame, text=f"Saving to: {save_directory}", font=ctk.CTkFont(size=11), text_color="gray")
folder_label.pack(side="left", padx=10)

progress_bar = ctk.CTkProgressBar(app, width=450)
progress_bar.pack(pady=(25, 10))
progress_bar.set(0) 

status_label = ctk.CTkLabel(app, text="Ready", text_color="gray", font=ctk.CTkFont(size=14))
status_label.pack(pady=5)

download_btn = ctk.CTkButton(app, text="Fetch Media", command=start_download, width=200, height=45, font=ctk.CTkFont(size=16, weight="bold"))
download_btn.pack(pady=20)

app.mainloop()