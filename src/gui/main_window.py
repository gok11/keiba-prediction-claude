"""
メインウィンドウモジュール
競馬予想アプリのメインウィンドウとタブ構成を管理
"""

from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QStatusBar, QMenuBar, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction

from src.gui.tabs.scraping_tab import ScrapingTab
from src.gui.tabs.data_viewer_tab import DataViewerTab
from src.gui.tabs.training_tab import TrainingTab
from src.gui.tabs.backtest_tab import BacktestTab
from src.gui.tabs.prediction_tab import PredictionTab
from src.database.db_manager import DatabaseManager


class MainWindow(QMainWindow):
    """メインウィンドウクラス"""

    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.init_ui()
        self.setup_menu()

    def init_ui(self):
        """UIの初期化"""
        self.setWindowTitle("競馬予想システム - Machine Learning Keiba Predictor")
        self.setGeometry(100, 100, 1400, 900)

        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # レイアウト
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # タブウィジェット
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # 各タブを追加
        self.scraping_tab = ScrapingTab(self.db_manager)
        self.data_viewer_tab = DataViewerTab()
        self.training_tab = TrainingTab(self.db_manager)
        self.backtest_tab = BacktestTab(self.db_manager)
        self.prediction_tab = PredictionTab(self.db_manager)

        self.tabs.addTab(self.scraping_tab, "📥 データ収集")
        self.tabs.addTab(self.data_viewer_tab, "📖 データ閲覧")
        self.tabs.addTab(self.training_tab, "🤖 トレーニング")
        self.tabs.addTab(self.backtest_tab, "📊 バックテスト")
        self.tabs.addTab(self.prediction_tab, "🎯 本番予想")

        # ステータスバー
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("準備完了")

        # スタイル設定
        self.apply_styles()

    def setup_menu(self):
        """メニューバーのセットアップ"""
        menubar = self.menuBar()

        # ファイルメニュー
        file_menu = menubar.addMenu("ファイル(&F)")

        # データベース初期化
        init_db_action = QAction("データベース初期化", self)
        init_db_action.triggered.connect(self.initialize_database)
        file_menu.addAction(init_db_action)

        file_menu.addSeparator()

        # 終了
        exit_action = QAction("終了(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # ヘルプメニュー
        help_menu = menubar.addMenu("ヘルプ(&H)")

        about_action = QAction("バージョン情報(&A)", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def initialize_database(self):
        """データベースを初期化"""
        reply = QMessageBox.question(
            self,
            'データベース初期化',
            'データベースを初期化しますか？\n（既存のデータは保持されます）',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db_manager.initialize_database()
                QMessageBox.information(self, "成功", "データベースの初期化に成功しました")
                self.status_bar.showMessage("データベースを初期化しました", 5000)
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"データベース初期化エラー:\n{str(e)}")

    def show_about(self):
        """バージョン情報を表示"""
        QMessageBox.about(
            self,
            "バージョン情報",
            "<h2>競馬予想システム</h2>"
            "<p>Version 1.0.0</p>"
            "<p>機械学習を用いた競馬予想アプリケーション</p>"
            "<p>© 2025</p>"
        )

    def apply_styles(self):
        """アプリケーションのスタイルを適用"""
        stylesheet = """
        QMainWindow {
            background-color: #f5f5f5;
        }

        QTabWidget::pane {
            border: 1px solid #cccccc;
            background-color: white;
            border-radius: 4px;
        }

        QTabBar::tab {
            background-color: #e0e0e0;
            color: #333333;
            padding: 10px 20px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            font-size: 14px;
            font-weight: bold;
        }

        QTabBar::tab:selected {
            background-color: white;
            color: #2196F3;
        }

        QTabBar::tab:hover {
            background-color: #d0d0d0;
        }

        QPushButton {
            background-color: #2196F3;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 13px;
            font-weight: bold;
        }

        QPushButton:hover {
            background-color: #1976D2;
        }

        QPushButton:pressed {
            background-color: #0D47A1;
        }

        QPushButton:disabled {
            background-color: #cccccc;
            color: #666666;
        }

        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
            padding: 6px;
            border: 1px solid #cccccc;
            border-radius: 4px;
            background-color: white;
            font-size: 13px;
        }

        QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
            border: 2px solid #2196F3;
        }

        QLabel {
            color: #333333;
            font-size: 13px;
        }

        QGroupBox {
            font-weight: bold;
            border: 2px solid #cccccc;
            border-radius: 6px;
            margin-top: 10px;
            padding-top: 10px;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }

        QProgressBar {
            border: 1px solid #cccccc;
            border-radius: 4px;
            text-align: center;
            font-weight: bold;
        }

        QProgressBar::chunk {
            background-color: #4CAF50;
            border-radius: 3px;
        }

        QTextEdit, QPlainTextEdit {
            border: 1px solid #cccccc;
            border-radius: 4px;
            background-color: white;
            font-family: 'Courier New', monospace;
            font-size: 12px;
        }

        QStatusBar {
            background-color: #e0e0e0;
            color: #333333;
        }
        """
        self.setStyleSheet(stylesheet)

    def closeEvent(self, event):
        """ウィンドウを閉じる際の処理"""
        reply = QMessageBox.question(
            self,
            '終了確認',
            'アプリケーションを終了しますか？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # データベース接続を切断
            self.db_manager.disconnect()
            event.accept()
        else:
            event.ignore()
