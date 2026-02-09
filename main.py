import tkinter as tk
from tkinter import messagebox
import pyautogui
import threading
import time
import os
import win32gui
import win32api
import win32con

# Pastikan folder ada
if not os.path.exists('image'):
    os.makedirs('image')

class FishingBotUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ROX Bot: Silent Mode")
        self.root.geometry("400x550")
        self.root.attributes('-topmost', True)

        self.is_running = False
        self.throw_region = None
        self.pull_region = None
        self.fish_count = 0

        # UI Header
        tk.Label(root, text="ROX SILENT CLICKER", font=('Arial', 14, 'bold'), fg="#8e44ad").pack(pady=10)
        tk.Label(root, text="Bot akan klik tanpa menggerakkan mouse.\nSyarat: Game jangan diminimize/ditutup.", font=('Arial', 9)).pack()

        # Buttons
        self.btn_throw = tk.Button(root, text="1. Set Area Lempar", command=lambda: self.start_capture("lempar"), bg="#f0f0f0")
        self.btn_throw.pack(pady=5, fill='x', padx=20)

        self.btn_pull = tk.Button(root, text="2. Set Area Tarik", command=lambda: self.start_capture("tarik"), bg="#f0f0f0")
        self.btn_pull.pack(pady=5, fill='x', padx=20)

        # Status
        self.status_label = tk.Label(root, text="Status: IDLE", font=('Arial', 10, 'bold'))
        self.status_label.pack(pady=10)
        
        self.counter_label = tk.Label(root, text="Ikan: 0", font=('Arial', 12), fg="green")
        self.counter_label.pack(pady=5)

        self.log_box = tk.Listbox(root, height=8, font=('Consolas', 9), bg="#2c3e50", fg="white")
        self.log_box.pack(pady=10, fill='both', padx=20)

        self.btn_start = tk.Button(root, text="START BOT", bg="green", fg="white", font=('Arial', 12, 'bold'), command=self.toggle_bot)
        self.btn_start.pack(pady=10, fill='x', padx=30)

    def log(self, message):
        self.log_box.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}")
        self.log_box.see(tk.END)

    def background_click(self, pos):
        """
        Mengirim sinyal klik langsung ke jendela game tanpa memindahkan mouse fisik.
        pos: tuple (x, y) koordinat layar global.
        """
        try:
            x, y = int(pos[0]), int(pos[1])
            
            # 1. Cari handle jendela (HWND) yang ada di posisi kursor target
            hwnd = win32gui.WindowFromPoint((x, y))
            
            # 2. Konversi koordinat Layar ke koordinat Client (Relatif terhadap jendela game)
            client_point = win32gui.ScreenToClient(hwnd, (x, y))
            
            # 3. Buat parameter posisi untuk pesan Windows (lParam)
            # MAKELONG menggabungkan X dan Y menjadi integer 32-bit
            lParam = win32api.MAKELONG(client_point[0], client_point[1])
            
            # 4. Kirim pesan KLIK TURUN dan KLIK NAIK ke jendela tersebut
            win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
            time.sleep(0.05) # Tahan sebentar
            win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lParam)
            
            # self.log(f"Silent click at {x},{y}") # Debugging
            
        except Exception as e:
            self.log(f"Click Error: {e}")

    def start_capture(self, mode):
        self.root.withdraw()
        time.sleep(0.5)
        capture_win = tk.Toplevel(self.root)
        capture_win.attributes('-alpha', 0.3, '-fullscreen', True, '-topmost', True)
        canvas = tk.Canvas(capture_win, cursor="cross", bg="grey")
        canvas.pack(fill="both", expand=True)
        rect = None
        start_x = start_y = 0

        def on_press(event):
            nonlocal start_x, start_y, rect
            start_x, start_y = event.x, event.y
            rect = canvas.create_rectangle(start_x, start_y, 1, 1, outline='red', width=2)

        def on_move(event):
            canvas.coords(rect, start_x, start_y, event.x, event.y)

        def on_release(event):
            end_x, end_y = event.x, event.y
            w = max(10, abs(end_x - start_x))
            h = max(10, abs(end_y - start_y))
            region = (min(start_x, end_x), min(start_y, end_y), w, h)
            
            pyautogui.screenshot(f'image/{mode}.png', region=region)
            
            if mode == "lempar":
                self.throw_region = region
                self.btn_throw.config(bg="#a29bfe", text="Area Lempar: OK")
            else:
                self.pull_region = region
                self.btn_pull.config(bg="#a29bfe", text="Area Tarik: OK")
                
            capture_win.destroy()
            self.root.deiconify()
            self.log(f"Capture {mode} OK.")

        canvas.bind("<ButtonPress-1>", on_press)
        canvas.bind("<B1-Motion>", on_move)
        canvas.bind("<ButtonRelease-1>", on_release)

    def is_ring_still_blue(self, region):
        try:
            screenshot = pyautogui.screenshot(region=region)
            w, h = screenshot.size
            cx, cy = w // 2, h // 2
            radius = int(min(w, h) * 0.40) 
            points = [(cx, cy-radius), (cx, cy+radius), (cx-radius, cy), (cx+radius, cy)]
            for px, py in points:
                r, g, b = screenshot.getpixel((px, py))
                # Jika ada elemen biru (lingkaran luar), berarti belum waktunya tarik
                if b > 160: return True
            return False
        except: return False

    def toggle_bot(self):
        if not self.is_running:
            if not self.throw_region or not self.pull_region:
                messagebox.showwarning("Error", "Set Area dulu!")
                return
            self.is_running = True
            self.btn_start.config(text="STOP", bg="#e74c3c")
            threading.Thread(target=self.bot_logic, daemon=True).start()
        else:
            self.is_running = False
            self.btn_start.config(text="START", bg="#2ecc71")

    def bot_logic(self):
        self.log("Silent Bot Running...")
        while self.is_running:
            try:
                # 1. CEK TARIK
                pull_pos = pyautogui.locateCenterOnScreen('image/tarik.png', region=self.pull_region, confidence=0.5, grayscale=True)
                
                if pull_pos:
                    if self.is_ring_still_blue(self.pull_region):
                        time.sleep(0.05)
                        continue 
                    else:
                        # GANTI KLIK BIASA DENGAN BACKGROUND CLICK
                        self.background_click(pull_pos)
                        
                        self.log("TARIK (Silent)!")
                        self.fish_count += 1
                        self.counter_label.config(text=f"Ikan: {self.fish_count}")
                        time.sleep(3)
                        continue

                # 2. CEK LEMPAR
                else:
                    throw_pos = pyautogui.locateCenterOnScreen('image/lempar.png', region=self.throw_region, confidence=0.6, grayscale=True)
                    if throw_pos:
                        # GANTI KLIK BIASA DENGAN BACKGROUND CLICK
                        self.background_click(throw_pos)
                        
                        self.log("Lempar (Silent)...")
                        time.sleep(2)

            except Exception as e:
                pass
            
            time.sleep(0.02)

if __name__ == "__main__":
    root = tk.Tk()
    app = FishingBotUI(root)
    root.mainloop()