"""
データ集約モジュール
すべての収集モジュールからデータを統合
"""

import time
from keystroke_collector import KeystrokeCollector
from mouse_collector import MouseCollector
from window_collector import WindowCollector
from environment_collector import EnvironmentCollector


class DataAggregator:
    """すべてのデータを集約"""

    def __init__(self, m5stack_port=None):
        """
        データ集約の初期化

        Args:
            m5stack_port: M5Stackのシリアルポート（Noneの場合はモックデータ）
        """
        print("=" * 60)
        print("データ収集モジュールを初期化しています...")
        print("=" * 60 + "\n")

        self.keystroke_collector = KeystrokeCollector()
        self.mouse_collector = MouseCollector()
        self.window_collector = WindowCollector()
        self.env_collector = EnvironmentCollector(port=m5stack_port)

        # バックグラウンド収集を開始
        self.keystroke_collector.start()
        self.mouse_collector.start()

        print("\n✓ すべてのモジュールを初期化しました\n")

    def collect_1min_data(self):
        """1分ごとにすべてのデータを集約"""
        try:
            # 各モジュールから統計を取得
            keystroke_stats = self.keystroke_collector.calculate_1min_stats()
            mouse_stats = self.mouse_collector.calculate_1min_stats()
            window_stats = self.window_collector.get_1min_stats()
            env_data = self.env_collector.get_latest_data()

            # 統合データ
            aggregated_data = {
                "system_time": time.time(),

                # キーストロークデータ
                "keystroke": keystroke_stats,

                # マウスデータ
                "mouse": mouse_stats,

                # ウィンドウデータ
                "window": window_stats,

                # 環境データ
                "environment": env_data
            }

            return aggregated_data

        except Exception as e:
            print(f"⚠ データ集約エラー: {e}")
            # エラーが発生してもNoneを返さず、空のデータを返す
            return {
                "system_time": time.time(),
                "keystroke": {},
                "mouse": {},
                "window": {},
                "environment": {}
            }

    def stop(self):
        """すべての収集を停止"""
        print("\n収集モジュールを停止しています...")
        self.keystroke_collector.stop()
        self.mouse_collector.stop()
        self.env_collector.close()
        print("✓ すべてのモジュールを停止しました")


# テスト実行
if __name__ == "__main__":
    print("=" * 60)
    print("データ集約テスト")
    print("=" * 60 + "\n")

    aggregator = DataAggregator()

    print("データ収集を開始します...")
    print("（Ctrl+Cで終了）\n")

    try:
        iteration = 0
        while True:
            time.sleep(10)  # 10秒ごとにテスト
            iteration += 1

            print(f"\n【{iteration}回目のデータ収集】")
            data = aggregator.collect_1min_data()

            # キーストロークデータ
            ks = data["keystroke"]
            print(f"✓ キーストローク: {ks.get('typing_speed_kpm', 0)} keys/min")

            # マウスデータ
            ms = data["mouse"]
            print(f"✓ マウス: {ms.get('movement_distance_px', 0):.0f}px, {ms.get('click_frequency', 0)}クリック")

            # ウィンドウデータ
            ws = data["window"]
            print(f"✓ ウィンドウ: {ws.get('work_category', 'unknown')} ({ws.get('window_switch_count', 0)}回切替)")

            # 環境データ
            env = data["environment"]
            is_mock = env.get("mock", False)
            status = "モック" if is_mock else "実データ"
            print(f"✓ 環境: {env.get('temperature', 0):.1f}℃, "
                  f"{env.get('humidity', 0):.1f}%, "
                  f"{env.get('pressure', 0):.1f}hPa ({status})")

    except KeyboardInterrupt:
        print("\n\nテストを終了します...")
        aggregator.stop()

