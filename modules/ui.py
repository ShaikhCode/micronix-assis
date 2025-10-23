# modules/ui_phase6.py
import os
import threading
import time
import collections
import numpy as np
import sounddevice as sd
from PIL import Image, ImageTk, ImageDraw, ImageFilter, ImageSequence
import customtkinter as ctk

from modules.listeners import listen_command
from modules.speaker import speak
from modules.commands import execute_command
from modules.system_info import get_system_info


# ---------- Utility: round-corner image ----------
def make_rounded_image(image_path, size=(50, 50), radius=6):
    img = Image.open(image_path).convert("RGBA").resize(size)
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, size[0], size[1]], radius=radius, fill=255)
    img.putalpha(mask)
    return img


# ---------- Load Animated GIF ----------
def load_gif_frames(path, max_frames=30, size=(250, 120)):
    frames = []
    try:
        im = Image.open(path)
        for i, frame in enumerate(ImageSequence.Iterator(im)):
            if i >= max_frames:
                break
            frame = frame.convert("RGBA").resize(size)
            frames.append(ImageTk.PhotoImage(frame))
    except Exception as e:
        print("GIF load error:", e)
    return frames


# ---------- Audio Visualizer ----------
class AudioVisualizer:
    def __init__(self, samplerate=44100, blocksize=1024, channels=1, buffer_seconds=1.5):
        self.sr = samplerate
        self.block = blocksize
        self.channels = channels
        self.buffer_len = int((buffer_seconds * samplerate) / blocksize)
        self.wave_deque = collections.deque(maxlen=self.buffer_len)
        self.rms = 0.0
        self.running = False
        self.stream = None

    def _callback(self, indata, frames, time_info, status):
        if status:
            pass
        mono = np.mean(indata, axis=1) if indata.ndim > 1 else indata
        block_rms = float(np.sqrt(np.mean(mono**2)))
        self.rms = block_rms
        self.wave_deque.append(mono.copy())

    def start(self, device=None):
        if self.running:
            return
        try:
            self.stream = sd.InputStream(channels=self.channels, callback=self._callback,
                                         blocksize=self.block, samplerate=self.sr, device=device)
            self.stream.start()
            self.running = True
        except Exception as e:
            print("AudioVisualizer start error:", e)
            self.running = False

    def stop(self):
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except:
                pass
        self.running = False
        self.wave_deque.clear()
        self.rms = 0.0

    def get_waveform(self, downsample=4, width_pixels=400):
        if not self.wave_deque:
            return np.zeros(width_pixels)
        arr = np.concatenate(list(self.wave_deque))
        if arr.size == 0:
            return np.zeros(width_pixels)
        arr = arr - np.mean(arr)
        maxv = np.max(np.abs(arr)) or 1e-9
        arr = arr / maxv
        idx = np.linspace(0, arr.size - 1, width_pixels).astype(int)
        sample = arr[idx]
        return sample

    def get_level(self):
        level = min(max(self.rms * 20.0, 0.0), 1.0)
        return level


# ---------- Main UI ----------
class MicronixPhase6UI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Micronix — AI Interface (Phase 6)")
        self.geometry("1100x700")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        # Theme Colors
        self.bg_main = "#0b0b0b"
        self.bg_panel = "#111111"
        self.accent = "#00bfff"
        self.text_color = "#e6e6e6"

        self.configure(fg_color=self.bg_main)

        # State
        self.is_listening = False
        self.visualizer = AudioVisualizer()
        self.update_interval = 40
        self.wave_width = 700
        self.wave_height = 120

        # Logo
        rounded_logo_img = ctk.CTkImage(make_rounded_image("assets/Micronix.png"), size=(50, 50))

        # Top bar
        self.top_frame = ctk.CTkFrame(self, corner_radius=0,fg_color="black")
        self.top_frame.pack(pady=(12, 6))

        self.logo_label = ctk.CTkLabel(self.top_frame, image=rounded_logo_img, text="")
        self.logo_label.pack(side="left", padx=(12, 6))

        self.title_label = ctk.CTkLabel(self.top_frame, text="M I C R O N I X  —  INTELLIGENT SYSTEM", font=("Orbitron", 36, "bold"))
        self.title_label.pack(side="left", padx=(6, 12))

        # Status bar
        self.status_frame = ctk.CTkFrame(self, corner_radius=12, fg_color=self.bg_panel)
        self.status_frame.pack(fill="x", padx=20, pady=6)
        self.status_label = ctk.CTkLabel(
            self.status_frame, text="Status: Idle", anchor="w", font=("Consolas", 14), text_color=self.text_color)
        self.status_label.pack(side="left", padx=12, pady=8)
        self.sys_label = ctk.CTkLabel(
            self.status_frame, text="", anchor="e", font=("Consolas", 12), text_color="#999")
        self.sys_label.pack(side="right", padx=12)

        # Main area
        self.main_frame = ctk.CTkFrame(self, corner_radius=12, fg_color=self.bg_panel)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=12)

        # Left panel
        self.left_panel = ctk.CTkFrame(self.main_frame, width=520, corner_radius=12, fg_color="black")
        self.left_panel.pack(side="left", fill="both", expand=False, padx=(12, 6), pady=12)

        # Voice GIF
        self.gif_frames = load_gif_frames("assets/voice.gif", size=(370, 300))
        self.gif_label = ctk.CTkLabel(self.left_panel, text="")
        self.gif_label.pack(pady=(16, 0))
        self._animate_gif_frame = 0
        self._animate_gif()

        # Waveform
        self.wave_canvas = ctk.CTkCanvas(
            self.left_panel, width=self.wave_width, height=self.wave_height,
            highlightthickness=0, bg="#0f1624"
        )
        self.wave_canvas.pack(pady=6)

        # Controls
        self.controls = ctk.CTkFrame(self.left_panel, fg_color=self.bg_panel)
        self.controls.pack(pady=10, padx=9)
        self.start_btn = ctk.CTkButton(
            self.controls, text="🟢 Start", fg_color=self.accent, hover_color="#0099cc",
            text_color="white", command=self.start_listening, width=150)
        self.start_btn.pack(side="left", padx=8)
        self.stop_btn = ctk.CTkButton(
            self.controls, text="🔴 Stop", fg_color="#b00020", hover_color="#ff0033",
            text_color="white", command=self.stop_listening, width=150)
        self.stop_btn.pack(side="left", padx=8)

        # Right panel - Chat log
        self.right_panel = ctk.CTkFrame(self.main_frame, corner_radius=12, fg_color=self.bg_main)
        self.right_panel.pack(side="right", fill="both", expand=True, padx=(6, 12), pady=12)
        self.chat_box = ctk.CTkTextbox(
            self.right_panel, width=500, height=480, fg_color="#0f0f0f",
            text_color=self.text_color, font=("Consolas", 14)
        )
        self.chat_box.pack(fill="both", expand=True, padx=12, pady=12)
        self.chat_box.insert("0.0", "Micronix: Online.\n\n")

        # Update loops
        self.after(self.update_interval, self._update_ui)
        threading.Thread(target=self._update_system_info_loop, daemon=True).start()

    # ---------- Animate GIF ----------
    def _animate_gif(self):
        if hasattr(self, "gif_frames") and self.gif_frames:
            frame = self.gif_frames[self._animate_gif_frame]
            self.gif_label.configure(image=frame)
            self._animate_gif_frame = (self._animate_gif_frame + 1) % len(self.gif_frames)
        self.after(80, self._animate_gif)

    # ---------- System Info ----------
    def _update_system_info_loop(self):
        while True:
            try:
                info = get_system_info()
                sys_text = " | ".join([f"{k}: {v}" for k, v in info.items()])
                self.after(0, lambda t=sys_text: self.sys_label.configure(text=t))
            except Exception:
                pass
            time.sleep(1)

    # ---------- Listening ----------
    def start_listening(self):
        if self.is_listening:
            return
        self.visualizer.start()
        self.is_listening = True
        self.status_label.configure(text="Status: Listening")
        threading.Thread(target=self._listen_loop, daemon=True).start()

    def stop_listening(self):
        if not self.is_listening:
            return
        self.is_listening = False
        self.visualizer.stop()
        self.status_label.configure(text="Status: Idle")

    # ---------- Listen Loop ----------
    def _listen_loop(self):
        while self.is_listening:
            self.after(0, lambda: self.chat_box.insert("end", "Micronix: Listening for command...\n"))
            command = listen_command()
            if not self.is_listening:
                break
            if command:
                self.after(0, lambda cmd=command: self.chat_box.insert("end", f"You: {cmd}\n"))
                self.after(0, lambda: self.status_label.configure(text="Status: Processing"))
                response = execute_command(command)
                self.after(0, lambda resp=response: self.chat_box.insert("end", f"Micronix: {resp}\n\n"))
                speak(response)
                self.after(0, lambda: self.status_label.configure(text="Status: Listening"))
            else:
                self.after(0, lambda: self.chat_box.insert("end", "Micronix: (no input detected)\n\n"))
                time.sleep(0.5)

    # ---------- UI Update ----------
    def _update_ui(self):
        level = self.visualizer.get_level() if self.visualizer.running else 0.0
        waveform = self.visualizer.get_waveform(width_pixels=self.wave_width)
        self._draw_waveform(waveform)
        self.after(self.update_interval, self._update_ui)

    # ---------- Waveform ----------
    def _draw_waveform(self, waveform):
        self.wave_canvas.delete("all")
        if waveform is None or len(waveform) == 0:
            return
        w, h = self.wave_width, self.wave_height
        center = h // 2
        amp = 0.9 * (h // 2)
        pts = [(i, int(center - v * amp)) for i, v in enumerate(waveform)]
        if pts:
            top = pts
            bottom = [(x, center + (center - y)) for (x, y) in reversed(pts)]
            all_pts = top + bottom
            flat = [coord for p in all_pts for coord in p]
            self.wave_canvas.create_polygon(flat, fill=self.accent, outline=self.accent)
        self.wave_canvas.create_line(0, center, w, center, fill="#0e2233")


if __name__ == "__main__":
    app = MicronixPhase6UI()
    app.mainloop()
