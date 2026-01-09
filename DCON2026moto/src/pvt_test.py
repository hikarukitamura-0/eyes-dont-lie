import tkinter as tk
import time
import random
import sqlite3
import sys
import statistics
import platform
import signal
import queue
from ctypes import windll
from pynput import keyboard

class PVTTest:
    """
    【ZoneKey PVT Module】
    - 集中度測定用モジュール
    - ステルス測定対応（作業用スレッドセーフ実装）
    - 結果はデータベース (zone_key_data.db) にのみ保存
    - ★修正: ユーザー指定の緩やかな判定基準に合わせてスコア計算を調整
    """

    def __init__(self, db_path="zone_key_data.db", root=None):
        if platform.system() == "Windows":
            try:
                windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                pass

        # ==========================================
        # ★設定エリア
        # ==========================================
        self.check_interval_min = 5   # 5分に1回
        self.trials_per_session = 3   # 3回計測
        self.window_size = 50         # インジケーターサイズ 50px
        
        # 待ち時間（2〜5秒のランダム）
        self.min_wait = 2000
        self.max_wait = 5000
        # ==========================================

        self.db_path = db_path
        self.setup_database()

        if root is None:
            self.root = tk.Tk()
            self.root.withdraw()
            self.standalone = True
        else:
            self.root = root
            self.standalone = False

        self.ui_queue = queue.Queue()
        self.root.after(100, self._process_queue)

        # 状態管理
        self.window = None
        self.canvas = None
        self.indicator = None
        self.current_trial = 0
        self.reaction_times = []
        self.stimulus_start_time = 0
        self.is_active = False
        self.listener = None
        self.running = True
        
        # 重複防止用
        self.scheduled_job = None
        self.is_session_running = False

    def setup_database(self):
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
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

    # ==========================================================
    #  制御メソッド
    # ==========================================================

    def start_monitoring(self):
        print(f"✅ PVT監視を開始 (間隔: {self.check_interval_min}分)")
        self.schedule_next_session()

    def show_test(self):
        """手動実行用"""
        if self.scheduled_job:
            self.root.after_cancel(self.scheduled_job)
            self.scheduled_job = None
        self.start_session()

    def schedule_next_session(self):
        """次回のテストを予約（重複防止）"""
        if not self.running: return

        if self.scheduled_job:
            self.root.after_cancel(self.scheduled_job)
            self.scheduled_job = None

        interval_ms = int(self.check_interval_min * 60 * 1000)
        self.scheduled_job = self.root.after(interval_ms, self.start_session)

    # ==========================================================
    #  テストセッション進行
    # ==========================================================

    def start_session(self):
        if not self.running: return
        
        # 重複実行ガード
        if self.is_session_running: return

        self.scheduled_job = None
        self.is_session_running = True

        if self.window: self.window.destroy()
        
        self.window = tk.Toplevel(self.root)
        self.window.title("ZoneKey")
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)

        transparent_color = "#123456"
        if platform.system() == "Windows":
            try:
                self.window.attributes('-transparentcolor', transparent_color)
            except Exception:
                pass

        w = self.window_size
        h = self.window_size
        
        self.canvas = tk.Canvas(self.window, width=w, height=h, bg=transparent_color, highlightthickness=0)
        self.canvas.pack()
        
        pad = 2
        self.indicator = self.canvas.create_oval(pad, pad, w-pad, h-pad, fill="#cccccc", outline="#999999", width=2)
        
        self.listener = keyboard.Listener(on_press=self.on_key_press)
        self.listener.start()
        
        self.current_trial = 0
        self.reaction_times = []
        
        self.run_next_trial()

    def run_next_trial(self):
        if not self.running: return
        
        if self.current_trial >= self.trials_per_session:
            self.finish_session()
            return

        self.current_trial += 1
        self.is_active = False
        self.canvas.itemconfig(self.indicator, fill="#cccccc", outline="#999999")
        
        self.randomize_position()

        delay = random.uniform(self.min_wait, self.max_wait)
        self.root.after(int(delay), self.show_stimulus)

    def randomize_position(self):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w = self.window_size
        h = self.window_size
        x = random.randint(0, sw - w)
        y = random.randint(0, sh - h)
        self.window.geometry(f"{w}x{h}+{x}+{y}")

    def show_stimulus(self):
        if not self.window: return
        self.canvas.itemconfig(self.indicator, fill="#ff0000", outline="#cc0000")
        self.stimulus_start_time = time.time()
        self.is_active = True

    # ==========================================================
    #  入力検知
    # ==========================================================

    def on_key_press(self, key):
        if not self.is_active: return
        try:
            if key == keyboard.Key.shift_r or key == keyboard.Key.space:
                self.record_reaction()
        except AttributeError:
            pass

    def record_reaction(self):
        rt_sec = time.time() - self.stimulus_start_time
        rt_ms = rt_sec * 1000
        
        if rt_ms < 100: return 
        
        self.reaction_times.append(rt_ms)
        self.is_active = False
        self.ui_queue.put("reaction_ok")

    def _process_queue(self):
        try:
            while True:
                msg = self.ui_queue.get_nowait()
                if msg == "reaction_ok":
                    self._handle_ui_update()
        except queue.Empty:
            pass
        
        if self.running:
            self.root.after(50, self._process_queue)

    def _handle_ui_update(self):
        if not self.window or not self.canvas: return
        self.canvas.itemconfig(self.indicator, fill="#00ff00", outline="#00cc00")
        self.root.update()
        self.root.after(500, self.run_next_trial)

    # ==========================================================
    #  終了処理・判定ロジック（再調整済み）
    # ==========================================================

    def finish_session(self):
        if self.window:
            self.window.destroy()
            self.window = None
        if self.listener:
            self.listener.stop()
            self.listener = None
        
        self.is_session_running = False

        if not self.reaction_times:
            self.schedule_next_session()
            return

        avg_rt = statistics.mean(self.reaction_times)
        
        # 判定を行う
        score = self.calculate_focus_score(avg_rt)
        alertness = self.get_alertness_level(avg_rt)
        
        # Lapse判定: 「低い」の基準に合わせて4500ms以上をLapse（集中切れ）とする
        # （以前の2000msだと「通常」評価なのにLapse判定されてしまうため）
        is_lapse = avg_rt >= 4500
        
        print(f"✅ PVT測定完了: 平均 {avg_rt:.1f}ms -> {alertness} (Score: {score:.2f})")

        self.save_data(avg_rt, score, alertness, is_lapse)
        self.schedule_next_session()

    def save_data(self, rt, score, level, lapse):
        ts = time.time()
        try:
            self.cursor.execute("""
                INSERT INTO pvt_results (
                    timestamp, stimulus_time, reaction_time_ms,
                    focus_score, alertness_level, is_lapse, false_start
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (ts, ts, rt, score, level, lapse, False))
            self.conn.commit()
        except Exception as e:
            print(f"⚠ DB保存失敗: {e}")

    def calculate_focus_score(self, rt_ms):
        """
        スコア計算（ユーザー指定の基準に合わせて調整）:
        - 400ms以下: 1.0 (満点)
        - 7000ms以上: 0.0 (非常に低いラインで0点になるように延長)
        """
        if rt_ms < 100: return 0.5
        
        if rt_ms <= 400: return 1.0
        
        # 7000ms以上で0点（以前は2000msでしたが、基準緩和に合わせました）
        if rt_ms >= 7000: return 0.0
        
        # 400〜7000の間で線形に減点 (分母は 7000-400 = 6600)
        return 1.0 - ((rt_ms - 400) / 6600)

    def get_alertness_level(self, rt_ms):
        # ★修正：ご指定の基準値
        if rt_ms < 1000: return "非常に高い"  # 〜1.0s （サクサク反応）
        if rt_ms < 2500: return "高い"      # 〜2.5s （順調）
        if rt_ms < 4500: return "通常"      # 〜4.5s （少し考え中〜普通）
        if rt_ms < 7000: return "低い"      # 〜7.0s （手が止まりがち）
        return "非常に低い"                 # 7.0s〜 （完全に停止）

    def close_db(self):
        try:
            self.conn.close()
        except:
            pass

def signal_handler(sig, frame):
    print("\n🛑 ユーザーによる中断 (Ctrl+C)")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    root = tk.Tk()
    root.withdraw()
    pvt = PVTTest(root=root)
    print("--- 起動確認: 5秒後に最初のテストを行います ---")
    pvt.root.after(5000, pvt.start_session)
    
    def check_loop():
        root.after(100, check_loop)
    root.after(100, check_loop)
    root.mainloop()