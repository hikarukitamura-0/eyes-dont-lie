"""
マウス動作収集モジュール
マウスの移動距離、クリック頻度、静止時間などを記録
"""

from pynput import mouse
import time
import math


class MouseCollector:
    """マウス動作データを収集"""

    def __init__(self):
        self.last_position = None
        self.total_distance = 0
        self.click_count = {"left": 0, "right": 0, "double": 0}
        self.last_move_time = time.time()
        self.still_time = 0
        self.listener = None

        # 1分間のリセット用
        self.last_reset_time = time.time()

    def on_move(self, x, y):
        """マウス移動イベント"""
        current_time = time.time()

        if self.last_position is not None:
            # 移動距離の計算
            distance = math.sqrt(
                (x - self.last_position[0])**2 +
                (y - self.last_position[1])**2
            )
            self.total_distance += distance

            # 静止時間の更新（移動があった場合はリセット）
            if distance > 5:  # 5px以上の移動
                time_diff = current_time - self.last_move_time
                if time_diff > 1.0:  # 1秒以上静止していた
                    self.still_time += time_diff
                self.last_move_time = current_time

        self.last_position = (x, y)

    def on_click(self, x, y, button, pressed):
        """マウスクリックイベント"""
        if pressed:
            if button == mouse.Button.left:
                self.click_count["left"] += 1
            elif button == mouse.Button.right:
                self.click_count["right"] += 1

    def on_scroll(self, x, y, dx, dy):
        """マウススクロールイベント（オプション）"""
        pass

    def start(self):
        """マウス動作収集を開始"""
        if self.listener is None:
            self.listener = mouse.Listener(
                on_move=self.on_move,
                on_click=self.on_click,
                on_scroll=self.on_scroll
            )
            self.listener.start()
            print("✓ マウス動作収集を開始しました")

    def stop(self):
        """マウス動作収集を停止"""
        if self.listener:
            self.listener.stop()
            self.listener = None
            print("マウス動作収集を停止しました")

    def calculate_1min_stats(self):
        """1分間のマウス動作統計を計算"""
        current_time = time.time()
        elapsed_time = current_time - self.last_reset_time

        # 静止時間の最終更新
        if current_time - self.last_move_time > 1.0:
            self.still_time += current_time - self.last_move_time - 1.0

        # 静止時間の割合（0.0-1.0）
        still_ratio = min(1.0, self.still_time / elapsed_time) if elapsed_time > 0 else 0

        # 移動速度（ピクセル/秒）
        movement_speed = self.total_distance / elapsed_time if elapsed_time > 0 else 0

        stats = {
            "movement_distance_px": self.total_distance,
            "movement_speed_px_per_sec": movement_speed,
            "click_frequency": sum(self.click_count.values()),
            "left_click_count": self.click_count["left"],
            "right_click_count": self.click_count["right"],
            "still_time_ratio": still_ratio,
            "timestamp": current_time
        }

        # カウンタリセット
        self.total_distance = 0
        self.click_count = {"left": 0, "right": 0, "double": 0}
        self.still_time = 0
        self.last_reset_time = current_time

        return stats


# テスト実行
if __name__ == "__main__":
    print("=" * 60)
    print("マウス動作収集テスト")
    print("=" * 60)
    print("\nマウスを動かしたり、クリックしてください...")
    print("（Ctrl+Cで終了）\n")

    collector = MouseCollector()
    collector.start()

    try:
        while True:
            time.sleep(10)
            stats = collector.calculate_1min_stats()
            print(f"\n【過去10秒間の統計】")
            print(f"  移動距離: {stats['movement_distance_px']:.0f}px")
            print(f"  移動速度: {stats['movement_speed_px_per_sec']:.0f}px/秒")
            print(f"  クリック回数: {stats['click_frequency']}回")
            print(f"  静止時間割合: {stats['still_time_ratio']:.2%}")
    except KeyboardInterrupt:
        print("\n\nテストを終了します...")
        collector.stop()

