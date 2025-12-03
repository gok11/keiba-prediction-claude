#!/usr/bin/env python3
"""
競馬予想システム - メインエントリーポイント
Machine Learning Keiba Predictor

機械学習を用いた競馬予想アプリケーション
"""

import sys
from pathlib import Path

# プロジェクトのルートディレクトリをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

from src.gui.main_window import MainWindow


def main():
    """メイン関数"""
    # アプリケーションの作成
    app = QApplication(sys.argv)

    # アプリケーション情報の設定
    app.setApplicationName("競馬予想システム")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Keiba ML")

    # High DPI対応
    app.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # メインウィンドウの作成と表示
    window = MainWindow()
    window.show()

    # イベントループの開始
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
