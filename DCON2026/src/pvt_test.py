import tkinter as tk
import time
import random
import sqlite3
import sys
import csv
import os
from datetime import datetime
from ctypes import windll

class PVTTest:
    """
    PVT（精神運動警戒検査）テストモジュール
    """

    def __init__(self, db_path="zone_key_data.db", root=None):
        try:
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

        self.db = sqlite3.connect(db_path)
        self.cursor = self.db.cursor()
        self.create_table()

        # 設定エリア
        self.size = 20          # 赤丸のサイズ
        self.min_wait = 300     # 300秒 = 5分
        self.max_wait = 300     # 300秒 = 5分
        self.timeout_sec = 10   # タイムアウト時間
        self.bg = "black"       
        self.csv_path = "pvt_backup.csv"

        if root is None:
            self.root = tk.Tk()
            self.root.withdraw()
            self.standalone = True
        else:
            self.root = root
            self.standalone = False

        self.window = None
        self.canvas = None
        self.stimulus_time = None
        self.running = False
        self.timeout_job = None
        
        self.init_csv()

    def create_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS pvt_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                stimulus_time REAL NOT NULL,
                reaction_time_ms REAL,
                focus_score REAL,
                alertness_level TEXT,
                is_lapse BOOLEAN,
                false_start BOOLEAN
            )
        """)
        self.db.commit()

    def init_csv(self):
        if not os.path.exists(self.csv_path):
            try:
                with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Timestamp", "RT_ms", "Alertness", "Focus_Score", "Note"])
            except Exception:
                pass

    def show_test(self):
        print(f"PVT監視を開始します（間隔: {self.min_wait}秒）")
        self.running = True
        self.setup_stealth_window()
        self.schedule_next()

    def setup_stealth_window(self):
        if self.window: return
        
        self.window = tk.Toplevel(self.root)
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        self.window.config(bg=self.bg)
        
        try:
            self.window.attributes('-transparentcolor', self.bg)
        except tk.TclError:
            print("透明化機能はサポートされていません")

        self.window.withdraw()
        
        self.canvas = tk.Canvas(self.window, width=self.size, height=self.size,
                                bg=self.bg, highlightthickness=0)
        self.canvas.pack()
        
        self.canvas.bind('<Button-1>', self.on_response)
        self.canvas.bind('<Button-3>', self.force_stop)

    def schedule_next(self):
        if not self.running: return
        
        wait_sec = random.uniform(self.min_wait, self.max_wait)
        self.root.after(int(wait_sec * 1000), self.show_stimulus)

    def show_stimulus(self):
        if not self.running: return

        self.canvas.delete("all")
        self.canvas.create_oval(0, 0, self.size, self.size, fill='red', outline='red')

        ws = self.root.winfo_screenwidth()
        hs = self.root.winfo_screenheight()
        
        margin = 50
        x = random.randint(margin, ws - self.size - margin)
        y = random.randint(margin, hs - self.size - margin)
        
        self.window.geometry(f"{self.size}x{self.size}+{x}+{y}")
        
        self.stimulus_time = time.time()
        self.window.deiconify()

        self.timeout_job = self.root.after(self.timeout_sec * 1000, self.on_timeout)

    def on_timeout(self):
        if not self.window.winfo_viewable(): return

        print("反応なし (Time out)")
        rt_ms = self.timeout_sec * 1000
        
        self.save_result(rt_ms, is_timeout=True)
        
        self.window.withdraw()
        self.schedule_next()

    def on_response(self, event):
        if self.stimulus_time is None: return
        
        if self.timeout_job:
            self.root.after_cancel(self.timeout_job)
            self.timeout_job = None
        
        rt_sec = time.time() - self.stimulus_time
        rt_ms = rt_sec * 1000

        print(f"PVT反応: {rt_ms:.0f}ms")
        self.save_result(rt_ms, is_timeout=False)
        
        self.window.withdraw()
        self.schedule_next()

    def save_result(self, rt_ms, is_timeout=False):
        focus_score = 0.0 if is_timeout else self.calculate_focus_score(rt_ms)
        alertness = "反応なし" if is_timeout else self.get_alertness_level(rt_ms)
        is_lapse = True if is_timeout or rt_ms > 1000 else False
        ts = time.time()

        try:
            self.cursor.execute("""
                INSERT INTO pvt_results (
                    timestamp, stimulus_time, reaction_time_ms,
                    focus_score, alertness_level, is_lapse, false_start
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (ts, self.stimulus_time, rt_ms, focus_score, alertness, is_lapse, False))
            self.db.commit()

            try:
                self.cursor.execute("""
                    UPDATE training_data
                    SET focus_score = ?
                    WHERE id = (SELECT MAX(id) FROM training_data)
                """, (focus_score,))
                self.db.commit()
            except sqlite3.OperationalError:
                pass
        except Exception as e:
            print(f"DB保存エラー: {e}")

        try:
            dt_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            note = "TIMEOUT" if is_timeout else ""
            with open(self.csv_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([dt_str, f"{rt_ms:.1f}", alertness, f"{focus_score:.2f}", note])
        except Exception as e:
            print(f"CSV保存エラー: {e}")

    def calculate_focus_score(self, rt_ms):
        if rt_ms is None: return 0.0
        if rt_ms < 200: return 0.5 
        if rt_ms < 650:   return 0.9 + (650 - rt_ms) / 1000
        elif rt_ms < 750: return 0.7 + (750 - rt_ms) / 500
        elif rt_ms < 900: return 0.5 + (900 - rt_ms) / 750
        elif rt_ms < 1100: return 0.3 + (1100 - rt_ms) / 1000
        else: return max(0.0, 0.3 - (rt_ms - 1100) / 2000)

    def get_alertness_level(self, rt_ms):
        if rt_ms is None: return "エラー"
        if rt_ms < 650: return "非常に高い"
        elif rt_ms < 750: return "高い"
        elif rt_ms < 900: return "通常"
        elif rt_ms < 1100: return "低い"
        else: return "非常に低い"

    def force_stop(self, event):
        print("PVTモニタリング終了")
        self.running = False
        self.window.destroy()
        self.close_db()
        sys.exit()

    def close_db(self):
        self.db.close()

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    
    pvt = PVTTest(root=root)
    pvt.show_test()
    root.mainloop()