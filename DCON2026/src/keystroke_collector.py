"""
キーストローク収集モジュール
プライバシー保護: キーの内容は記録せず、タイミング情報のみを記録
"""

from pynput import keyboard
import time
import numpy as np
from collections import deque


class KeystrokeCollector:
    """キーストローク・ダイナミクスを収集"""

    def __init__(self):
        self.last_key_time = None
        self.last_key_press_time = {}
        self.key_events = deque(maxlen=1000)  # 最新1000イベントを保持
        self.listener = None

    def on_press(self, key):
        """キー押下イベント"""
        current_time = time.time()

        key_data = {
            "timestamp": current_time,
            "event_type": "press",
            "is_backspace": key in [keyboard.Key.backspace, keyboard.Key.delete],
            "is_modifier": key in [keyboard.Key.ctrl, keyboard.Key.shift,
                                  keyboard.Key.alt, keyboard.Key.cmd,
                                  keyboard.Key.ctrl_l, keyboard.Key.ctrl_r,
                                  keyboard.Key.shift_l, keyboard.Key.shift_r]
        }

        # 打鍵間隔の計算
        if self.last_key_time is not None:
            key_data["key_interval_ms"] = (current_time - self.last_key_time) * 1000

        # キー押下開始時刻を記録
        try:
            key_id = str(key)
            self.last_key_press_time[key_id] = current_time
        except:
            pass

        self.key_events.append(key_data)
        self.last_key_time = current_time

    def on_release(self, key):
        """キー解放イベント"""
        current_time = time.time()

        # キー押下時間の計算
        try:
            key_id = str(key)
            if key_id in self.last_key_press_time:
                press_duration = (current_time - self.last_key_press_time[key_id]) * 1000

                # 押下時間を記録
                key_data = {
                    "timestamp": current_time,
                    "event_type": "release",
                    "key_press_duration_ms": press_duration
                }
                self.key_events.append(key_data)

                # クリーンアップ
                del self.last_key_press_time[key_id]
        except:
            pass

    def start(self):
        """キーストローク収集を開始"""
        if self.listener is None:
            self.listener = keyboard.Listener(
                on_press=self.on_press,
                on_release=self.on_release
            )
            self.listener.start()
            print("✓ キーストローク収集を開始しました")

    def stop(self):
        """キーストローク収集を停止"""
        if self.listener:
            self.listener.stop()
            self.listener = None
            print("キーストローク収集を停止しました")

    def calculate_1min_stats(self):
        """1分間のキーストローク統計を計算"""
        current_time = time.time()
        recent_events = [e for e in self.key_events
                        if current_time - e["timestamp"] <= 60]

        if len(recent_events) == 0:
            return {
                "typing_speed_kpm": 0,
                "avg_key_interval_ms": 0,
                "std_key_interval_ms": 0,
                "max_key_interval_ms": 0,
                "min_key_interval_ms": 0,
                "mistype_frequency": 0,
                "avg_key_press_duration_ms": 0,
                "timestamp": current_time
            }

        # 打鍵間隔の統計
        intervals = [e["key_interval_ms"] for e in recent_events
                    if "key_interval_ms" in e]

        # 押下時間の統計
        press_durations = [e["key_press_duration_ms"] for e in recent_events
                          if "key_press_duration_ms" in e]

        # ミスタッチ頻度
        mistype_count = sum(1 for e in recent_events
                           if e.get("is_backspace", False))

        return {
            "typing_speed_kpm": len([e for e in recent_events if e["event_type"] == "press"]),
            "avg_key_interval_ms": np.mean(intervals) if intervals else 0,
            "std_key_interval_ms": np.std(intervals) if intervals else 0,
            "max_key_interval_ms": max(intervals) if intervals else 0,
            "min_key_interval_ms": min(intervals) if intervals else 0,
            "mistype_frequency": mistype_count,
            "avg_key_press_duration_ms": np.mean(press_durations) if press_durations else 0,
            "timestamp": current_time
        }


# テスト実行
if __name__ == "__main__":
    print("=" * 60)
    print("キーストローク収集テスト")
    print("=" * 60)
    print("\n何かキーを入力してください...")
    print("（Ctrl+Cで終了）\n")

    collector = KeystrokeCollector()
    collector.start()

    try:
        while True:
            time.sleep(10)
            stats = collector.calculate_1min_stats()
            print(f"\n【過去1分間の統計】")
            print(f"  タイピング速度: {stats['typing_speed_kpm']} keys/min")
            print(f"  平均打鍵間隔: {stats['avg_key_interval_ms']:.0f}ms")
            print(f"  ミスタッチ頻度: {stats['mistype_frequency']}回")
    except KeyboardInterrupt:
        print("\n\nテストを終了します...")
        collector.stop()

