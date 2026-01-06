# Zone Key - データ収集プログラム

<div align="center">

**NASA・米軍で使用される PVT（精神運動警戒検査）を用いた科学的な集中度測定システム**

</div>

---

## 概要

Zone Key は、ディープラーニングモデルの学習に必要なデータセットを収集するためのプログラムです。キーストローク、マウス動作、ウィンドウ情報、環境データを収集し、**PVT（Psychomotor Vigilance Test）**による客観的な集中度測定を行います。

### 主な特徴

- **科学的根拠**: NASA・米軍で使用される PVT による集中度測定
- **プライバシー保護**: キーの内容は記録せず、タイミング情報のみを記録
- **自動収集**: バックグラウンドで継続的にデータを収集
- **客観的評価**: 反応時間（150-1000ms）から集中度スコア（0.0-1.0）を算出

---

## セットアップ

### 1. 依存パッケージのインストール

```bash
# 仮想環境を作成（推奨）
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# または
.venv\Scripts\activate  # Windows

# 依存パッケージをインストール
pip install -r requirements.txt
```

### 2. 動作確認

#### PVT テストの単体実行

```bash
cd src
python main.py --test-pvt
```

#### 各モジュールの個別テスト

```bash
# キーストローク収集テスト
python keystroke_collector.py

# マウス動作収集テスト
python mouse_collector.py

# ウィンドウ情報収集テスト
python window_collector.py

# 環境データ収集テスト
python environment_collector.py
```

---

## 使用方法

### 基本的な使用方法

```bash
cd src
python main.py
```

### M5Stack ENV III Unit を使用する場合

```bash
# macOS
python main.py --m5stack /dev/tty.usbserial-xxxxx

# Windows
python main.py --m5stack COM3
```

### プログラムの終了

`Ctrl+C` でプログラムを終了できます。

---

## PVT（精神運動警戒検査）について

### PVT とは

画面中央に表示される小さなウィンドウに 🔴（赤い円）が表示されたら、**できるだけ早くスペースキーを押す**。その反応時間（ミリ秒）を測定することで、覚醒度・集中度を客観的に評価する手法です。

- **ウィンドウサイズ**: 400×300 ピクセル（作業の邪魔にならないサイズ）
- **表示位置**: 画面中央、最前面
- **待機時間**: 0.5-1.5 秒（最小限の待機で素早くテスト）
- **測定方法**: 赤い円が表示されてからスペースキーを押すまでの時間

### 判定基準

| 反応時間   | 集中度スコア | 判定       |
| :--------- | :----------- | :--------- |
| 150-250ms  | 0.9-1.0      | Deep Focus |
| 250-350ms  | 0.7-0.9      | Focused    |
| 350-500ms  | 0.5-0.7      | Open       |
| 500-700ms  | 0.3-0.5      | Distracted |
| 700ms 以上 | 0.0-0.3      | Overheat   |

### テスト実行頻度

- **5 分ごと**に自動実行
- 頻繁なテストにより、集中度の変化を詳細に追跡

---

## 収集されるデータ

### 1. キーストロークデータ

- タイピング速度（KPM: Keys Per Minute）
- 打鍵間隔の平均・標準偏差
- ミスタッチ頻度（Backspace/Delete の使用回数）
- キー押下時間

**⚠ プライバシー保護**: キーの内容（文字）は**一切記録されません**

### 2. マウス動作データ

- マウス移動距離（ピクセル）
- クリック頻度（左/右クリック）
- 静止時間の割合

### 3. ウィンドウ情報

- アクティブウィンドウのハッシュ値（SHA-256）
- 作業カテゴリ（開発/コミュニケーション/ブラウジング/その他）
- ウィンドウ切り替え頻度

### 4. 環境データ

- 室温（℃）
- 湿度（%）
- 気圧（hPa）

**注**: M5Stack ENV III Unit が接続されていない場合は、モックデータを使用します。

### 5. PVT テスト結果

- 反応時間（ミリ秒）
- 集中度スコア（0.0-1.0）
- 覚醒度レベル

---

## データベース構造

データは `zone_key_data.db`（SQLite）に保存されます。

### テーブル構成

#### `training_data`

1 分ごとの集約データ

- キーストロークデータ（8 カラム）
- マウスデータ（6 カラム）
- ウィンドウデータ（3 カラム）
- 環境データ（3 カラム）
- ラベルデータ（2 カラム）

#### `pvt_results`

PVT テスト結果

- timestamp: テスト実施時刻
- reaction_time_ms: 反応時間（ミリ秒）
- focus_score: 集中度スコア（0.0-1.0）
- alertness_level: 覚醒度レベル
- is_lapse: ラプス（500ms 以上）かどうか

---

## データのエクスポート

### CSV 形式でエクスポート

```python
from data_storage import DataStorage

storage = DataStorage()

# 基本的なエクスポート
storage.export_to_csv("training_data.csv")

# PVTデータを統合したエクスポート
storage.export_pvt_dataset("dataset_pvt.csv")

storage.close()
```

---

## データ収集目標

### Phase 1: 初期データ収集（2 週間）

| 期間       | 目標                                                  |
| :--------- | :---------------------------------------------------- |
| **1 週目** | 5 名 × 1 日 8 時間 × 5 日 = **200 時間分**            |
| **2 週目** | 5 名 × 1 日 8 時間 × 5 日 = **200 時間分**            |
| **合計**   | **400 時間分**のデータ + **4800 回以上**の PVT テスト |

---

## プライバシー保護

### 実装済み対策

1. **キー内容を記録しない**

   - 打鍵のタイミング情報のみを記録
   - 文字コードや文字列は一切取得しない

2. **ウィンドウ名のハッシュ化**

   - アクティブウィンドウのタイトルを SHA-256 でハッシュ化
   - 元のタイトルを復元不可能

3. **ローカルストレージ**
   - データは全てローカルに保存
   - クラウド送信は匿名化後のみ

---

## 🛠 トラブルシューティング

### よくある問題

| 問題                             | 原因                         | 解決策                                        |
| :------------------------------- | :--------------------------- | :-------------------------------------------- |
| **キーストロークが取得できない** | 管理者権限が必要             | 管理者権限でプログラムを実行                  |
| **M5Stack が接続できない**       | シリアルポートが間違っている | デバイスマネージャーで正しいポートを確認      |
| **ウィンドウ情報が取得できない** | ライブラリが未インストール   | `pip install pyobjc-framework-Cocoa`（macOS） |

### 管理者権限での実行方法

**macOS/Linux:**

```bash
sudo python src/main.py
```

**Windows:**

1. コマンドプロンプトを右クリック
2. 「管理者として実行」を選択
3. `python src/main.py` を実行

---

## 参考資料

### PVT 関連

- **Dinges, D. F., & Powell, J. W. (1985).** "Microcomputer analyses of performance on a portable, simple visual RT task during sustained operations."
- **NASA Human Research Program**: PVT を宇宙飛行士の疲労測定に使用
- **米国防総省**: 兵士の覚醒度管理に PVT を採用

### 技術ドキュメント

- [pynput 公式ドキュメント](https://pynput.readthedocs.io/)
- [M5Stack 公式サイト](https://m5stack.com/)
- [SQLite 公式ドキュメント](https://www.sqlite.org/docs.html)

---

## ライセンス

このプロジェクトは教育目的で作成されています。

---

## 開発チーム

DCON2026 - Zone Key プロジェクト

---

## サポート

問題が発生した場合は、以下を確認してください：

1. `docs/データセット収集プログラム設計書.md` - 詳細な設計書
2. `docs/集中度測定方法の詳細設計.md` - PVT の詳細

---

<div align="center">

**Zone Key - 科学的根拠に基づいた集中度管理システム**

Made with for DCON2026

</div>
