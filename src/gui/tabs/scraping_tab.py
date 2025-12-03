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


class ScrapingTab(QWidget):
    """データ収集タブ"""

    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.scraping_thread = None
        self.init_ui()

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

        # 並行処理設定
        parallel_layout = QHBoxLayout()
        parallel_layout.addWidget(QLabel("並行処理数:"))

        self.parallel_count = QSpinBox()
        self.parallel_count.setRange(1, 5)
        self.parallel_count.setValue(1)
        parallel_layout.addWidget(self.parallel_count)
        parallel_layout.addWidget(QLabel("(推奨: 1-2, IPブロックに注意)"))
        parallel_layout.addStretch()
        settings_layout.addLayout(parallel_layout)

        # 血統情報取得オプション
        pedigree_layout = QHBoxLayout()
        self.fetch_pedigree = QCheckBox("血統情報を取得する（追加リクエストが必要）")
        self.fetch_pedigree.setChecked(False)
        pedigree_layout.addWidget(self.fetch_pedigree)
        pedigree_layout.addWidget(QLabel("※リクエスト数が大幅に増えます"))
        pedigree_layout.addStretch()
        settings_layout.addLayout(pedigree_layout)

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
            'parallel_count': self.parallel_count.value(),
            'fetch_pedigree': self.fetch_pedigree.isChecked()
        }

        self.add_log(f"期間: {config['start_date']} ～ {config['end_date']}")
        self.add_log(f"スリープ時間: {config['sleep_min']}～{config['sleep_max']}秒")
        self.add_log(f"並行処理数: {config['parallel_count']}")
        self.add_log(f"血統情報取得: {'有効' if config['fetch_pedigree'] else '無効'}")
        if config['fetch_pedigree']:
            self.add_log("⚠️  血統情報取得が有効です。リクエスト数が増加します。")
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
