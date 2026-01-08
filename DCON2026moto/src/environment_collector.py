"""
環境データ収集モジュール
M5Stack ENV III Unitから温度・湿度・気圧を取得
"""

import serial
import json
import time


class EnvironmentCollector:
    """環境データ（温度・湿度・気圧）を収集"""

    def __init__(self, port=None, baudrate=115200):
        """
        M5Stack ENV III Unitとのシリアル通信を初期化

        Args:
            port: シリアルポート
                  - macOS: "/dev/tty.usbserial-xxxxx" or "/dev/cu.usbserial-xxxxx"
                  - Windows: "COM3", "COM4", etc.
                  - None の場合は自動検出を試みる
            baudrate: ボーレート（デフォルト: 115200）
        """
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.last_data = {
            "temperature": 25.0,  # デフォルト値
            "humidity": 50.0,
            "pressure": 1013.25
        }

        # M5Stackに接続を試みる
        if port:
            self.connect(port, baudrate)

    def connect(self, port, baudrate=115200):
        """M5Stackに接続"""
        try:
            self.serial = serial.Serial(port, baudrate, timeout=1)
            print(f"✓ M5Stack ENV III Unit接続成功: {port}")
            return True
        except serial.SerialException as e:
            print(f"⚠ M5Stack接続エラー: {e}")
            print(f"  ポート {port} に接続できませんでした")
            print("  モックデータを使用します")
            self.serial = None
            return False
        except Exception as e:
            print(f"⚠ 予期しないエラー: {e}")
            self.serial = None
            return False

    def auto_detect_port(self):
        """シリアルポートを自動検出（実装予定）"""
        import serial.tools.list_ports

        ports = list(serial.tools.list_ports.comports())
        print("利用可能なシリアルポート:")
        for port in ports:
            print(f"  - {port.device}: {port.description}")

        # M5Stackっぽいポートを探す
        for port in ports:
            if "usb" in port.device.lower() or "serial" in port.device.lower():
                print(f"\n試行: {port.device}")
                if self.connect(port.device):
                    return True

        return False

    def read_sensor_data(self):
        """センサーデータを読み取り"""
        if self.serial and self.serial.in_waiting > 0:
            try:
                line = self.serial.readline().decode('utf-8').strip()
                data = json.loads(line)

                # データを更新
                self.last_data = {
                    "temperature": data.get("temp", self.last_data["temperature"]),
                    "humidity": data.get("humidity", self.last_data["humidity"]),
                    "pressure": data.get("pressure", self.last_data["pressure"]),
                    "timestamp": time.time()
                }

                return self.last_data

            except json.JSONDecodeError:
                # JSON解析エラー（不完全なデータなど）
                pass
            except Exception as e:
                print(f"センサーデータ読み取りエラー: {e}")

        # M5Stackが接続されていない場合はモックデータ
        return {
            "temperature": self.last_data["temperature"],
            "humidity": self.last_data["humidity"],
            "pressure": self.last_data["pressure"],
            "timestamp": time.time(),
            "mock": True  # モックデータであることを示す
        }

    def get_latest_data(self):
        """最新の環境データを取得"""
        return self.read_sensor_data()

    def close(self):
        """シリアル接続を閉じる"""
        if self.serial:
            self.serial.close()
            print("M5Stack接続を閉じました")


# テスト実行
if __name__ == "__main__":
    print("=" * 60)
    print("環境データ収集テスト")
    print("=" * 60)

    # ポートを指定（環境に応じて変更してください）
    # macOS: "/dev/tty.usbserial-xxxxx" or "/dev/cu.usbserial-xxxxx"
    # Windows: "COM3", "COM4", etc.
    port = None  # 自動検出を試みる

    collector = EnvironmentCollector(port=port)

    # 自動検出を試みる
    if not collector.serial:
        print("\nシリアルポートの自動検出を試みます...")
        collector.auto_detect_port()

    print("\n環境データを取得します...")
    print("（Ctrl+Cで終了）\n")

    try:
        while True:
            data = collector.get_latest_data()
            is_mock = data.get("mock", False)
            status = "（モックデータ）" if is_mock else "（実データ）"

            print(f"\r温度: {data['temperature']:.1f}℃ | "
                  f"湿度: {data['humidity']:.1f}% | "
                  f"気圧: {data['pressure']:.1f}hPa {status}", end="")

            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\nテストを終了します...")
        collector.close()

