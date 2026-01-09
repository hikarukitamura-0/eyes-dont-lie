"""
Zone Key - データ収集プログラム
キーストローク、マウス、ウィンドウ、環境データ + PVTテストによる集中度測定
"""

import time
import random
import threading
import tkinter as tk
from datetime import datetime
from data_aggregator import DataAggregator
from data_storage import DataStorage
from pvt_test import PVTTest


class ZoneKeyDataCollector:
    """Zone Key データ収集メインシステム"""

    def __init__(self, m5stack_port=None):
        """
        データ収集システムの初期化

        Args:
            m5stack_port: M5Stackのシリアルポート（Noneの場合はモックデータ）
        """
        print("\n" + "=" * 60)
        print("          Zone Key データ収集システム v2.0")
        print("=" * 60 + "\n")

        # メインのTkインスタンスを作成（非表示）
        self.root = tk.Tk()
        self.root.withdraw()  # メインウィンドウは非表示
        
        # モジュールの初期化
        self.aggregator = DataAggregator(m5stack_port=m5stack_port)
        self.storage = DataStorage()
        self.pvt = PVTTest(root=self.root)
        self.running = False

        # 次のPVTテスト実行時刻（5分後）
        first_test_delay = 5 * 60  # 5分
        self.next_pvt_time = time.time() + first_test_delay

        # PVTテスト実行フラグ（メインスレッドで実行するため）
        self.should_run_pvt = False

        print(f"📅 初回PVTテスト予定: {time.strftime('%H:%M:%S', time.localtime(self.next_pvt_time))}")
        print(f"   （{first_test_delay/60:.1f}分後）\n")

    def collect_loop(self):
        """1分ごとにデータ収集"""
        print("📊 データ収集ループを開始します...\n")

        while self.running:
            try:
                # 通常のデータ収集
                data = self.aggregator.collect_1min_data()
                success = self.storage.save_data(data)

                if success:
                    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    print(f"✓ [{current_time}] データ保存完了")
                else:
                    print(f"⚠ データ保存に失敗しました")

                # PVTテストの実行判定
                current_time_sec = time.time()
                if current_time_sec >= self.next_pvt_time:
                    # メインスレッドで実行するためにフラグを立てる
                    self.should_run_pvt = True

                    # 次のテスト時刻を設定（5分後）
                    next_delay = 5 * 60  # 5分
                    self.next_pvt_time = time.time() + next_delay
                    next_test_time = time.strftime('%H:%M:%S', time.localtime(self.next_pvt_time))
                    print(f"\n📅 次回PVTテスト予定: {next_test_time} ({next_delay/60:.1f}分後)\n")

            except Exception as e:
                print(f"⚠ エラー: {e}")

            time.sleep(60)  # 1分待機

    def run_pvt_test(self):
        """PVTテストを実行"""
        print("\n" + "=" * 60)
        print("🔴 PVTテスト開始（集中度測定）")
        print("=" * 60)
        print("\n指示:")
        print("  - 🔴が表示されたら、できるだけ早くスペースキーを押してください")
        print("  - ESCキーでテストをスキップできます\n")

        # メインスレッドでGUIを実行
        self.pvt.show_test()

    def display_statistics(self):
        """統計情報を表示"""
        print("\n" + "=" * 60)
        print("📈 データ収集統計")
        print("=" * 60)

        stats = self.storage.get_statistics()
        if stats:
            print(f"\n✓ 収集データ数: {stats['training_data_count']}レコード")
            print(f"✓ PVTテスト回数: {stats['pvt_test_count']}回")

            if stats['pvt_test_count'] > 0:
                avg_rt = stats['avg_reaction_time_ms']
                print(f"✓ 平均反応時間: {avg_rt:.0f}ms")

                # 覚醒度の判定
                if avg_rt < 250:
                    level = "非常に高い"
                elif avg_rt < 350:
                    level = "高い"
                elif avg_rt < 500:
                    level = "通常"
                elif avg_rt < 700:
                    level = "低い"
                else:
                    level = "非常に低い"

                print(f"✓ 全体的な覚醒度: {level}")

        print("\n" + "=" * 60 + "\n")

    def start(self):
        """データ収集開始"""
        self.running = True

        print("=" * 60)
        print("データ収集を開始します")
        print("=" * 60)
        print(f"\n⚠ 重要:")
        print("  - PVTテスト実行中は作業を中断し、テストに集中してください")
        print("  - テストは5分ごとに実行されます")
        print("  - ESCキーでテストをスキップできます")
        print(f"\n📅 次回PVTテスト: {time.strftime('%H:%M:%S', time.localtime(self.next_pvt_time))}")
        print("\n" + "=" * 60 + "\n")

        # バックグラウンドスレッドで収集ループを実行
        thread = threading.Thread(target=self.collect_loop, daemon=True)
        thread.start()

        try:
            # メインスレッドでPVTテストを実行（GUIはメインスレッドでのみ動作）
            while True:
                if self.should_run_pvt:
                    self.should_run_pvt = False
                    self.run_pvt_test()
                
                # Tkinterのイベントを処理（重要！）
                try:
                    self.root.update()
                except:
                    pass
                
                time.sleep(0.01)  # 10msごとにチェック

        except KeyboardInterrupt:
            print("\n\n" + "=" * 60)
            print("データ収集を停止します...")
            print("=" * 60)
            self.stop()

    def stop(self):
        """データ収集停止"""
        self.running = False

        print("\nAI学習用データセットを生成しています...")
        self.storage.export_pvt_dataset()

        # 統計情報を表示
        self.display_statistics()

        # クリーンアップ
        self.aggregator.stop()
        self.storage.close()
        self.pvt.close_db()
        
        # Tkinterのクリーンアップ
        try:
            self.root.quit()
            self.root.destroy()
        except:
            pass

        print("✓ すべてのモジュールを停止しました")
        print("\nプログラムを終了します。")


def main():
    """メイン関数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Zone Key データ収集プログラム"
    )
    parser.add_argument(
        "--m5stack",
        type=str,
        default=None,
        help="M5Stackのシリアルポート (例: /dev/tty.usbserial-xxxxx, COM3)"
    )
    parser.add_argument(
        "--test-pvt",
        action="store_true",
        help="PVTテストのみを実行（データ収集はしない）"
    )

    args = parser.parse_args()

    # PVTテストのみを実行
    if args.test_pvt:
        print("=" * 60)
        print("PVTテスト単体実行モード")
        print("=" * 60 + "\n")
        pvt = PVTTest()
        pvt.show_test()
        pvt.close_db()
        return

    # 通常のデータ収集モード
    collector = ZoneKeyDataCollector(m5stack_port=args.m5stack)
    collector.start()


if __name__ == "__main__":
    main()

