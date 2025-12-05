"""
スクレイピングタブ
db.netkeiba.comからレースデータを収集するUI
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QSpinBox, QDoubleSpinBox,
    QProgressBar, QTextEdit, QDateEdit, QMessageBox, QCheckBox
)
from PyQt6.QtCore import QDate, QThread, pyqtSignal
from datetime import datetime

from src.scraper.scraping_worker import ScrapingWorker
from src.utils.config import Config


class ScrapingTab(QWidget):
    """データ収集タブ"""

    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.scraping_thread = None
        self.config = Config()
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # 設定グループ
        settings_group = QGroupBox("スクレイピング設定")
        settings_layout = QVBoxLayout()
        settings_group.setLayout(settings_layout)

        # 期間設定
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("期間:"))

        self.start_date = QDateEdit()
        self.start_date.setDate(QDate(2020, 1, 1))
        self.start_date.setCalendarPopup(True)
        date_layout.addWidget(QLabel("開始日:"))
        date_layout.addWidget(self.start_date)

        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        date_layout.addWidget(QLabel("終了日:"))
        date_layout.addWidget(self.end_date)

        date_layout.addStretch()
        settings_layout.addLayout(date_layout)

        # スリープ時間設定
        sleep_layout = QHBoxLayout()
        sleep_layout.addWidget(QLabel("スリープ時間:"))

        self.sleep_min = QDoubleSpinBox()
        self.sleep_min.setRange(0.5, 10.0)
        self.sleep_min.setValue(2.0)
        self.sleep_min.setSuffix(" 秒")
        sleep_layout.addWidget(QLabel("最小:"))
        sleep_layout.addWidget(self.sleep_min)

        self.sleep_max = QDoubleSpinBox()
        self.sleep_max.setRange(0.5, 10.0)
        self.sleep_max.setValue(5.0)
        self.sleep_max.setSuffix(" 秒")
        sleep_layout.addWidget(QLabel("最大:"))
        sleep_layout.addWidget(self.sleep_max)

        sleep_layout.addStretch()
        settings_layout.addLayout(sleep_layout)

        # 血統情報取得オプション
        pedigree_layout = QHBoxLayout()
        self.fetch_pedigree = QCheckBox("血統情報を取得する（追加リクエストが必要）")
        self.fetch_pedigree.setChecked(True)  # デフォルトで有効
        pedigree_layout.addWidget(self.fetch_pedigree)
        pedigree_layout.addWidget(QLabel("※リクエスト数が大幅に増えます"))
        pedigree_layout.addStretch()
        settings_layout.addLayout(pedigree_layout)

        # プレミアム調教情報取得オプション
        premium_training_layout = QHBoxLayout()
        self.fetch_premium_training = QCheckBox("プレミアム調教情報を取得する（追加リクエストが必要）")
        self.fetch_premium_training.setChecked(True)  # デフォルトで有効
        premium_training_layout.addWidget(self.fetch_premium_training)
        premium_training_layout.addWidget(QLabel("※各馬ごとに2リクエスト増えます"))
        premium_training_layout.addStretch()
        settings_layout.addLayout(premium_training_layout)

        layout.addWidget(settings_group)

        # コントロールボタン
        control_layout = QHBoxLayout()

        self.start_button = QPushButton("スクレイピング開始")
        self.start_button.clicked.connect(self.start_scraping)
        control_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("中止")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_scraping)
        control_layout.addWidget(self.stop_button)

        control_layout.addStretch()
        layout.addLayout(control_layout)

        # プログレスバー
        progress_group = QGroupBox("進捗状況")
        progress_layout = QVBoxLayout()
        progress_group.setLayout(progress_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("待機中...")
        progress_layout.addWidget(self.progress_label)

        layout.addWidget(progress_group)

        # ログ表示
        log_group = QGroupBox("ログ")
        log_layout = QVBoxLayout()
        log_group.setLayout(log_layout)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)

        layout.addWidget(log_group)

    def start_scraping(self):
        """スクレイピングを開始"""
        # 日付の検証
        if self.start_date.date() > self.end_date.date():
            QMessageBox.warning(self, "入力エラー", "開始日は終了日より前に設定してください")
            return

        # スリープ時間の検証
        if self.sleep_min.value() > self.sleep_max.value():
            QMessageBox.warning(self, "入力エラー", "最小スリープ時間は最大スリープ時間以下に設定してください")
            return

        # UIの更新
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setValue(0)
        self.log_text.clear()
        self.add_log("スクレイピングを開始します...")

        # 設定の取得
        config = {
            'start_date': self.start_date.date().toString("yyyy-MM-dd"),
            'end_date': self.end_date.date().toString("yyyy-MM-dd"),
            'sleep_min': self.sleep_min.value(),
            'sleep_max': self.sleep_max.value(),
            'fetch_pedigree': self.fetch_pedigree.isChecked(),
            'fetch_premium_training': self.fetch_premium_training.isChecked()
        }

        self.add_log(f"期間: {config['start_date']} ～ {config['end_date']}")
        self.add_log(f"スリープ時間: {config['sleep_min']}～{config['sleep_max']}秒")
        self.add_log(f"血統情報取得: {'有効' if config['fetch_pedigree'] else '無効'}")
        self.add_log(f"プレミアム調教情報取得: {'有効' if config['fetch_premium_training'] else '無効'}")
        self.add_log("=" * 50)

        # スクレイピングワーカーの作成と起動
        self.scraping_thread = ScrapingWorker(self.db_manager, config)

        # シグナルの接続
        self.scraping_thread.progress_updated.connect(self.on_progress_updated)
        self.scraping_thread.log_message.connect(self.add_log)
        self.scraping_thread.scraping_finished.connect(self.on_scraping_finished)
        self.scraping_thread.scraping_error.connect(self.on_scraping_error)

        # スレッド開始
        self.scraping_thread.start()

    def stop_scraping(self):
        """スクレイピングを中止"""
        self.add_log("スクレイピングを中止しています...")

        if self.scraping_thread and self.scraping_thread.isRunning():
            self.scraping_thread.stop()
            self.scraping_thread.wait()

        self.add_log("中止しました")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def on_progress_updated(self, current: int, total: int, message: str):
        """進捗更新ハンドラ"""
        if total > 0:
            progress = int((current / total) * 100)
            self.progress_bar.setValue(progress)
            self.progress_label.setText(f"{current}/{total} - {message}")

    def on_scraping_finished(self, stats: dict):
        """スクレイピング完了ハンドラ"""
        self.progress_bar.setValue(100)
        self.progress_label.setText("完了")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        QMessageBox.information(
            self,
            "スクレイピング完了",
            f"スクレイピングが完了しました！\n\n"
            f"総リクエスト数: {stats['total_requests']}\n"
            f"保存されたレース数: {stats['races_saved']}\n"
            f"スキップされたレース数: {stats['races_skipped']}\n"
            f"保存された結果数: {stats['results_saved']}"
        )

    def on_scraping_error(self, error_message: str):
        """エラーハンドラ"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        QMessageBox.critical(self, "エラー", error_message)

    def add_log(self, message: str):
        """ログにメッセージを追加"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
    def load_settings(self):
        """保存された設定を読み込む"""
        try:
            # 期間設定の読み込み
            start_date_str = self.config.get('scraping.start_date', '2020-01-01')
            end_date_str = self.config.get('scraping.end_date', QDate.currentDate().toString('yyyy-MM-dd'))
            
            start_date = QDate.fromString(start_date_str, 'yyyy-MM-dd')
            end_date = QDate.fromString(end_date_str, 'yyyy-MM-dd')
            
            if start_date.isValid():
                self.start_date.setDate(start_date)
            if end_date.isValid():
                self.end_date.setDate(end_date)
            
            # スリープ時間の読み込み
            sleep_min = self.config.get('scraping.sleep_min', 2.0)
            sleep_max = self.config.get('scraping.sleep_max', 5.0)
            
            self.sleep_min.setValue(sleep_min)
            self.sleep_max.setValue(sleep_max)
            
            # 値が変更されたときに保存するように接続
            self.start_date.dateChanged.connect(self.save_settings)
            self.end_date.dateChanged.connect(self.save_settings)
            self.sleep_min.valueChanged.connect(self.save_settings)
            self.sleep_max.valueChanged.connect(self.save_settings)
            
        except Exception:
            # 読み込みに失敗してもデフォルト値で続行
            pass
    
    def save_settings(self):
        """設定を保存する"""
        try:
            self.config.set('scraping.start_date', self.start_date.date().toString('yyyy-MM-dd'))
            self.config.set('scraping.end_date', self.end_date.date().toString('yyyy-MM-dd'))
            self.config.set('scraping.sleep_min', self.sleep_min.value())
            self.config.set('scraping.sleep_max', self.sleep_max.value())
        except Exception:
            # 保存に失敗してもエラーは無視（次回保存時に再試行）
            pass
