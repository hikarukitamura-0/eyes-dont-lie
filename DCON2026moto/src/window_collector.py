"""
ウィンドウ情報収集モジュール
アクティブウィンドウと作業カテゴリを記録（プライバシー保護: ハッシュ化）
"""

import hashlib
import time
import platform

# プラットフォームに応じたウィンドウ取得ライブラリ
system = platform.system()

if system == "Darwin":  # macOS
    try:
        from AppKit import NSWorkspace
        MACOS_AVAILABLE = True
    except ImportError:
        MACOS_AVAILABLE = False
        print("警告: macOSでAppKitが利用できません。pip install pyobjcを実行してください。")
elif system == "Windows":  # Windows
    try:
        import pygetwindow as gw
        WINDOWS_AVAILABLE = True
    except ImportError:
        WINDOWS_AVAILABLE = False
        print("警告: Windowsでpygetwindowが利用できません。pip install pygetwindowを実行してください。")
else:  # Linux
    LINUX_AVAILABLE = False
    print("警告: Linuxは現在サポートされていません。")


# 作業カテゴリの分類ルール
CATEGORY_RULES = {
    "development": ["Visual Studio Code", "PyCharm", "IntelliJ", "Xcode", "Terminal",
                   "iTerm", "Code", "Sublime", "Atom", "Eclipse", "NetBeans"],
    "communication": ["Slack", "Discord", "Teams", "Zoom", "Mail", "Messages",
                     "Skype", "LINE", "Telegram", "WhatsApp"],
    "browsing": ["Chrome", "Firefox", "Safari", "Edge", "Brave", "Opera"],
    "document": ["Word", "Excel", "PowerPoint", "Pages", "Numbers", "Keynote",
                "Google Docs", "Google Sheets"],
    "other": []  # デフォルト
}


class WindowCollector:
    """ウィンドウ情報を収集"""

    def __init__(self):
        self.window_switches = 0
        self.last_window = None
        self.last_check_time = time.time()

    def get_active_window_macos(self):
        """macOSでアクティブウィンドウを取得"""
        if not MACOS_AVAILABLE:
            return None

        try:
            workspace = NSWorkspace.sharedWorkspace()
            active_app = workspace.activeApplication()
            if active_app:
                app_name = active_app['NSApplicationName']
                return app_name
        except Exception as e:
            print(f"macOSウィンドウ取得エラー: {e}")
            return None

    def get_active_window_windows(self):
        """Windowsでアクティブウィンドウを取得"""
        if not WINDOWS_AVAILABLE:
            return None

        try:
            active_window = gw.getActiveWindow()
            if active_window:
                return active_window.title
        except Exception as e:
            print(f"Windowsウィンドウ取得エラー: {e}")
            return None

    def get_active_window(self):
        """プラットフォームに応じてアクティブウィンドウを取得"""
        system = platform.system()

        if system == "Darwin":  # macOS
            window_title = self.get_active_window_macos()
        elif system == "Windows":  # Windows
            window_title = self.get_active_window_windows()
        else:
            window_title = None

        if not window_title:
            return None

        # プライバシー保護: ウィンドウタイトルをハッシュ化
        window_hash = hashlib.sha256(window_title.encode()).hexdigest()[:16]

        # カテゴリ分類
        category = self.classify_category(window_title)

        # ウィンドウ切り替え検出
        if self.last_window != window_hash:
            self.window_switches += 1
            self.last_window = window_hash

        return {
            "window_hash": window_hash,
            "work_category": category,
            "timestamp": time.time()
        }

    def classify_category(self, window_title):
        """ウィンドウタイトルから作業カテゴリを分類"""
        window_title_lower = window_title.lower()

        for category, keywords in CATEGORY_RULES.items():
            if category == "other":
                continue
            if any(keyword.lower() in window_title_lower for keyword in keywords):
                return category

        return "other"

    def get_1min_stats(self):
        """1分間のウィンドウ統計"""
        current_window = self.get_active_window()

        stats = {
            "window_switch_count": self.window_switches,
            "timestamp": time.time()
        }

        # 現在のウィンドウ情報を追加
        if current_window:
            stats["window_hash"] = current_window["window_hash"]
            stats["work_category"] = current_window["work_category"]
        else:
            stats["window_hash"] = "unknown"
            stats["work_category"] = "other"

        # カウンタリセット
        self.window_switches = 0

        return stats


# テスト実行
if __name__ == "__main__":
    print("=" * 60)
    print("ウィンドウ情報収集テスト")
    print("=" * 60)
    print(f"\nプラットフォーム: {platform.system()}")
    print("\nウィンドウを切り替えてください...")
    print("（Ctrl+Cで終了）\n")

    collector = WindowCollector()

    try:
        while True:
            time.sleep(5)
            window_info = collector.get_active_window()
            if window_info:
                print(f"アクティブウィンドウ: {window_info['window_hash']} (カテゴリ: {window_info['work_category']})")
            else:
                print("ウィンドウ情報を取得できませんでした")

            stats = collector.get_1min_stats()
            print(f"  切り替え回数: {stats['window_switch_count']}回\n")
    except KeyboardInterrupt:
        print("\n\nテストを終了します...")

