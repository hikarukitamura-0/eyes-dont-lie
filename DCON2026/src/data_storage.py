"""
データ保存モジュール
SQLiteデータベースにデータを保存
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime


class DataStorage:
    """データベース保存"""

    def __init__(self, db_path="zone_key_data.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()
        print(f"✓ データベース接続: {db_path}")

    def create_tables(self):
        """テーブル作成"""
        # メインの学習データテーブル
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS training_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,

                -- キーストロークデータ
                typing_speed_kpm INTEGER,
                avg_key_interval_ms REAL,
                std_key_interval_ms REAL,
                max_key_interval_ms REAL,
                min_key_interval_ms REAL,
                mistype_frequency INTEGER,
                avg_key_press_duration_ms REAL,

                -- マウスデータ
                movement_distance_px REAL,
                movement_speed_px_per_sec REAL,
                click_frequency INTEGER,
                left_click_count INTEGER,
                right_click_count INTEGER,
                still_time_ratio REAL,

                -- ウィンドウデータ
                window_hash TEXT,
                work_category TEXT,
                window_switch_count INTEGER,

                -- 環境データ
                temperature REAL,
                humidity REAL,
                pressure REAL,

                -- ラベルデータ（PVTから自動取得）
                focus_score REAL,
                state_label TEXT
            )
        """)

        # PVTテスト結果テーブル
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

        # ユーザープロファイルテーブル
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profile (
                user_id TEXT PRIMARY KEY,
                age INTEGER,
                occupation TEXT,
                typing_skill TEXT,
                baseline_rt_median REAL,
                baseline_rt_std REAL,
                created_at REAL
            )
        """)

        self.conn.commit()
        print("✓ データベーステーブルを作成しました")

    def save_data(self, data):
        """集約データを保存"""
        try:
            keystroke = data.get("keystroke", {})
            mouse = data.get("mouse", {})
            window = data.get("window", {})
            environment = data.get("environment", {})

            self.cursor.execute("""
                INSERT INTO training_data (
                    timestamp,
                    typing_speed_kpm, avg_key_interval_ms, std_key_interval_ms,
                    max_key_interval_ms, min_key_interval_ms, mistype_frequency,
                    avg_key_press_duration_ms,
                    movement_distance_px, movement_speed_px_per_sec,
                    click_frequency, left_click_count,
                    right_click_count, still_time_ratio,
                    window_hash, work_category, window_switch_count,
                    temperature, humidity, pressure
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get("system_time"),
                keystroke.get("typing_speed_kpm"),
                keystroke.get("avg_key_interval_ms"),
                keystroke.get("std_key_interval_ms"),
                keystroke.get("max_key_interval_ms"),
                keystroke.get("min_key_interval_ms"),
                keystroke.get("mistype_frequency"),
                keystroke.get("avg_key_press_duration_ms"),
                mouse.get("movement_distance_px"),
                mouse.get("movement_speed_px_per_sec"),
                mouse.get("click_frequency"),
                mouse.get("left_click_count"),
                mouse.get("right_click_count"),
                mouse.get("still_time_ratio"),
                window.get("window_hash"),
                window.get("work_category"),
                window.get("window_switch_count"),
                environment.get("temperature"),
                environment.get("humidity"),
                environment.get("pressure")
            ))
            self.conn.commit()
            return True

        except Exception as e:
            print(f"⚠ データ保存エラー: {e}")
            return False

    def export_to_csv(self, output_path="training_data.csv"):
        """学習用にCSV形式でエクスポート"""
        try:
            df = pd.read_sql_query("SELECT * FROM training_data", self.conn)
            df.to_csv(output_path, index=False)
            print(f"✓ データをエクスポート: {output_path}")
            print(f"  総レコード数: {len(df)}")
            return True
        except Exception as e:
            print(f"⚠ CSVエクスポートエラー: {e}")
            return False

    def export_pvt_dataset(self, output_path="dataset_pvt.csv"):
        """PVTデータを含む学習用データセットをエクスポート"""
        try:
            query = """
                SELECT
                    t.timestamp,
                    t.typing_speed_kpm,
                    t.avg_key_interval_ms,
                    t.std_key_interval_ms,
                    t.mistype_frequency,
                    t.movement_distance_px,
                    t.click_frequency,
                    t.work_category,
                    t.window_switch_count,
                    t.temperature,
                    t.humidity,
                    t.pressure,
                    p.reaction_time_ms AS pvt_rt,
                    p.focus_score AS pvt_focus_score,
                    p.alertness_level,
                    p.is_lapse AS pvt_lapse,
                    p.focus_score AS target_focus_score,
                    CASE
                        WHEN p.focus_score > 0.7 THEN 'Deep Focus'
                        WHEN p.focus_score >= 0.3 THEN 'Open'
                        ELSE 'Overheat'
                    END AS target_state
                FROM training_data t
                LEFT JOIN (
                    SELECT
                        *,
                        ROW_NUMBER() OVER (
                            PARTITION BY CAST(timestamp / 3600 AS INTEGER)
                            ORDER BY timestamp DESC
                        ) as rn
                    FROM pvt_results
                    WHERE reaction_time_ms IS NOT NULL
                ) p ON p.rn = 1
                WHERE p.reaction_time_ms IS NOT NULL
                ORDER BY t.timestamp
            """

            df = pd.read_sql_query(query, self.conn)

            # 作業カテゴリのOne-Hot Encoding
            df = pd.get_dummies(df, columns=['work_category'])

            # 時刻のCyclical Encoding
            df['hour_sin'] = np.sin(2 * np.pi * df['timestamp'].apply(
                lambda x: datetime.fromtimestamp(x).hour) / 24)
            df['hour_cos'] = np.cos(2 * np.pi * df['timestamp'].apply(
                lambda x: datetime.fromtimestamp(x).hour) / 24)

            # CSV出力
            df.to_csv(output_path, index=False)

            print(f"✓ PVTデータセット生成完了: {output_path}")
            print(f"  総サンプル数: {len(df)}")
            print(f"  特徴量数: {len(df.columns) - 2}")  # ターゲット変数を除く

            # データ分布の確認
            if len(df) > 0:
                print("\n【集中度スコアの分布】")
                print(df['target_focus_score'].describe())
                print("\n【状態ラベルの分布】")
                print(df['target_state'].value_counts())

            return True

        except Exception as e:
            print(f"⚠ PVTデータセットエクスポートエラー: {e}")
            return False

    def get_statistics(self):
        """データベースの統計情報を取得"""
        try:
            # training_dataのレコード数
            self.cursor.execute("SELECT COUNT(*) FROM training_data")
            training_count = self.cursor.fetchone()[0]

            # pvt_resultsのレコード数
            self.cursor.execute("SELECT COUNT(*) FROM pvt_results")
            pvt_count = self.cursor.fetchone()[0]

            # PVTの平均反応時間
            self.cursor.execute("""
                SELECT AVG(reaction_time_ms)
                FROM pvt_results
                WHERE reaction_time_ms IS NOT NULL
            """)
            avg_rt = self.cursor.fetchone()[0]

            return {
                "training_data_count": training_count,
                "pvt_test_count": pvt_count,
                "avg_reaction_time_ms": avg_rt if avg_rt else 0
            }

        except Exception as e:
            print(f"⚠ 統計情報取得エラー: {e}")
            return None

    def close(self):
        """データベース接続を閉じる"""
        self.conn.close()
        print("✓ データベース接続を閉じました")


# テスト実行
if __name__ == "__main__":
    print("=" * 60)
    print("データ保存テスト")
    print("=" * 60 + "\n")

    storage = DataStorage("test_zone_key_data.db")

    # テストデータを保存
    test_data = {
        "system_time": 1702300845.123,
        "keystroke": {
            "typing_speed_kpm": 120,
            "avg_key_interval_ms": 200,
            "std_key_interval_ms": 50,
            "max_key_interval_ms": 500,
            "min_key_interval_ms": 100,
            "mistype_frequency": 5,
            "avg_key_press_duration_ms": 80
        },
        "mouse": {
            "movement_distance_px": 5000,
            "movement_speed_px_per_sec": 100,
            "click_frequency": 10,
            "left_click_count": 8,
            "right_click_count": 2,
            "still_time_ratio": 0.3
        },
        "window": {
            "window_hash": "a3f5b2c1",
            "work_category": "development",
            "window_switch_count": 5
        },
        "environment": {
            "temperature": 24.5,
            "humidity": 50.2,
            "pressure": 1013.25
        }
    }

    print("テストデータを保存しています...")
    if storage.save_data(test_data):
        print("✓ テストデータを保存しました")

    print("\n統計情報を取得しています...")
    stats = storage.get_statistics()
    if stats:
        print(f"✓ training_data: {stats['training_data_count']}レコード")
        print(f"✓ pvt_results: {stats['pvt_test_count']}レコード")
        print(f"✓ 平均反応時間: {stats['avg_reaction_time_ms']:.0f}ms")

    print("\nCSVエクスポートを試行しています...")
    storage.export_to_csv("test_export.csv")

    storage.close()
    print("\nテスト完了")

