import tkinter as tk
import time
import random
import sqlite3
import sys
import csv
import os
import statistics
from datetime import datetime
from ctypes import windll

class PVTTest:
    """
    【本番用】PVTテストモジュール (ZoneKey Production)
    - 5分に1回、強制的にチェック
    - 3回計測 → 平均値を記録
    - データベースの形式を厳守
    """

    def __init__(self, db_path="zone_key_data.db", root=None):
        try:
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

        # ==========================================
        # ★設定エリア
        # ==========================================
        self.check_interval_min = 5   # 【修正】5分に1回
        self.countdown_sec = 3        # 開始前のカウントダウン
        self.trials_per_session = 3   # 3回計測
        self.circle_radius = 30       # 赤丸サイズ
        self.wait_time_ms = 3000      # 待ち時間（3秒固定）
        # ==========================================

        self.db_path = db_path
        self.csv_path = "pvt_backup.csv"      # 元のバックアップ用
        self.dataset_path = "final_dataset.csv" # 学習用

        self.setup_database()
        self.init_csv()

        if root is None:
            self.root = tk.Tk()
            self.root.withdraw()
        else:
            self.root = root

        self.window = None
        self.canvas = None
        self.current_trial = 0
        self.reaction_times = []
        self.stimulus_start_time = 0
        self.is_waiting_for_response = False
        self.countdown_job = None
        self.timer_label = None

    def setup_database(self):
        """元のデータベース形式に合わせてテーブル作成"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            # あなたの元のコードの形式に合わせました
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
            self.conn.commit()
        except Exception as e:
            print(f"⚠ DB接続エラー: {e}")

    def init_csv(self):
        """CSVファイルの準備"""
        # 1. バックアップ用 (元の形式)
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "RT_ms", "Alertness", "Focus_Score", "Note"])

        # 2. 学習データセット用
        if not os.path.exists(self.dataset_path):
            with open(self.dataset_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "pvt_rt", "alertness_level", "target_focus_score", "note"])

    # =========================================================================
    #  スケジュール管理
    # =========================================================================
    def start_monitoring(self):
        print(f"✅ PVT監視を開始 (間隔: {self.check_interval_min}分)")
        self.schedule_next_session()

    def schedule_next_session(self):
        interval_ms = int(self.check_interval_min * 60 * 1000)
        print(f"⏳ 待機中... ({self.check_interval_min}分)")
        self.root.after(interval_ms, self.show_countdown_dialog)

    # =========================================================================
    #  画面処理 (カウントダウン -> テスト)
    # =========================================================================
    def show_countdown_dialog(self):
        if self.window: self.window.destroy()

        self.window = tk.Toplevel(self.root)
        self.window.title("ZoneKey Check")
        self.window.attributes('-topmost', True)
        
        ws = self.root.winfo_screenwidth()
        hs = self.root.winfo_screenheight()
        w, h = 400, 220
        x = (ws/2) - (w/2)
        y = (hs/2) - (h/2)
        self.window.geometry(f'{int(w)}x{int(h)}+{int(x)}+{int(y)}')
        
        tk.Label(self.window, text="⚠ 集中度チェックの時間です", font=("Meiryo", 14, "bold"), fg="#FF5722").pack(pady=15)
        
        self.remaining_sec = self.countdown_sec
        self.timer_label = tk.Label(self.window, text=f"あと {self.remaining_sec} 秒で開始します...", font=("Meiryo", 16))
        self.timer_label.pack(pady=10)
        
        tk.Label(self.window, text="準備ができたらスペースキーを押してください", font=("Meiryo", 10)).pack(pady=5)
        
        btn = tk.Button(self.window, text="今すぐ開始 (Space)", command=self.start_session, bg="#4CAF50", fg="white", font=("Meiryo", 11, "bold"))
        btn.pack(pady=10)

        self.window.bind('<space>', lambda e: self.start_session())
        self.window.protocol("WM_DELETE_WINDOW", lambda: None) 

        self.update_countdown()

    def update_countdown(self):
        if not self.window: return
        if self.remaining_sec > 0:
            self.remaining_sec -= 1
            self.timer_label.config(text=f"あと {self.remaining_sec} 秒で開始します...")
            self.countdown_job = self.window.after(1000, self.update_countdown)
        else:
            self.start_session()

    def start_session(self):
        if self.countdown_job:
            self.window.after_cancel(self.countdown_job)
        if self.window:
            self.window.destroy()
        
        self.window = tk.Toplevel(self.root)
        self.window.attributes('-fullscreen', True)
        self.window.attributes('-topmost', True)
        self.window.configure(bg='black')
        
        self.canvas = tk.Canvas(self.window, bg='black', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        
        self.window.bind('<space>', self.on_user_reaction)
        self.window.bind('<Escape>', lambda e: self.force_stop()) 

        self.current_trial = 0
        self.reaction_times = []
        self.run_next_trial()

    def run_next_trial(self):
        if self.current_trial >= self.trials_per_session:
            self.finish_session()
            return

        self.current_trial += 1
        self.is_waiting_for_response = False
        
        self.canvas.delete("all")
        msg = f"Check {self.current_trial} / {self.trials_per_session}\n..."
        self.canvas.create_text(self.root.winfo_screenwidth()//2, self.root.winfo_screenheight()//2, 
                                text=msg, fill="gray", font=("Arial", 20))

        self.root.after(self.wait_time_ms, self.show_stimulus)

    def show_stimulus(self):
        if not self.window: return
        self.canvas.delete("all")
        cx = self.root.winfo_screenwidth() // 2
        cy = self.root.winfo_screenheight() // 2
        r = self.circle_radius
        self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, fill='red', outline='red')
        self.stimulus_start_time = time.time()
        self.is_waiting_for_response = True

    def on_user_reaction(self, event):
        if not self.is_waiting_for_response: return 
        rt_sec = time.time() - self.stimulus_start_time
        rt_ms = rt_sec * 1000
        self.reaction_times.append(rt_ms)
        self.is_waiting_for_response = False
        self.canvas.delete("all")
        self.canvas.create_text(self.root.winfo_screenwidth()//2, self.root.winfo_screenheight()//2, 
                                text=f"{rt_ms:.0f}", fill="white", font=("Arial", 30))
        self.root.after(800, self.run_next_trial)

    # =========================================================================
    #  保存処理 (ここを修正しました)
    # =========================================================================
    def finish_session(self):
        if self.window:
            self.window.destroy()
            self.window = None

        if not self.reaction_times:
            self.schedule_next_session()
            return

        avg_rt = statistics.mean(self.reaction_times)
        score = self.calculate_focus_score(avg_rt)
        alertness = self.get_alertness_level(avg_rt)
        is_lapse = avg_rt > 500
        
        print(f"✅ 測定完了: 平均 {avg_rt:.1f}ms -> スコア {score:.2f}")

        # 保存実行
        self.save_data(avg_rt, score, alertness, is_lapse)
        self.schedule_next_session()

    def save_data(self, rt, score, level, lapse):
        ts = time.time()
        
        # 1. データベースへの保存（元のカラム定義を厳守）
        # stimulus_time は平均なので計測時刻と同じにします
        # false_start は UI側で制御しているので False で固定
        try:
            self.cursor.execute("""
                INSERT INTO pvt_results (
                    timestamp, stimulus_time, reaction_time_ms,
                    focus_score, alertness_level, is_lapse, false_start
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (ts, ts, rt, score, level, lapse, False))
            self.conn.commit()
            print("   -> DB保存完了")
        except Exception as e:
            print(f"⚠ DB保存失敗: {e}")

        # 2. バックアップCSV (元の形式)
        try:
            dt_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(self.csv_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([dt_str, f"{rt:.1f}", level, f"{score:.2f}", "3-Trial-Avg"])
        except Exception as e:
            print(f"⚠ CSV保存失敗: {e}")

        # 3. 学習用データセット (AI用形式)
        try:
            with open(self.dataset_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([ts, f"{rt:.2f}", level, f"{score:.4f}", "3-Trial-Avg"])
        except Exception as e:
            pass

    def calculate_focus_score(self, rt_ms):
        if rt_ms < 150: return 0.5 
        if rt_ms <= 300: return 1.0 
        if rt_ms >= 1000: return 0.0 
        return 1.0 - ((rt_ms - 300) / 700)

    def get_alertness_level(self, rt_ms):
        if rt_ms < 250: return "Deep Focus"
        if rt_ms < 350: return "Focus"
        if rt_ms < 500: return "Normal"
        if rt_ms < 1000: return "Drowsy"
        return "Sleepy"

    def force_stop(self):
        if self.window: self.window.destroy()
        try:
            self.conn.close()
        except:
            pass
        sys.exit()

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    pvt = PVTTest(root=root)
    
    # 動作確認: 最初の1回だけ5秒後にテスト (2回目以降は5分後)
    print("--- 起動確認: 5秒後に最初のテストを行います ---")
    pvt.root.after(5000, pvt.show_countdown_dialog)
    root.mainloop()