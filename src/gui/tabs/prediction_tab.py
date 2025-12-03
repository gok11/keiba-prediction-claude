"""
予想タブ
本番のレースに対して予想を実行するUI
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QTextEdit,
    QDateEdit
)
from PyQt6.QtCore import QDate, Qt
from datetime import datetime


class PredictionTab(QWidget):
    """本番予想タブ"""

    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.init_ui()

    def init_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # モデル選択と対象日設定
        settings_group = QGroupBox("予想設定")
        settings_layout = QVBoxLayout()
        settings_group.setLayout(settings_layout)

        # モデル選択
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("使用モデル:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["モデルファイルを選択..."])
        # TODO: 訓練済みモデルのリストを読み込む
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()
        settings_layout.addLayout(model_layout)

        # 対象日選択
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("対象日:"))
        self.target_date = QDateEdit()
        self.target_date.setDate(QDate.currentDate())
        self.target_date.setCalendarPopup(True)
        date_layout.addWidget(self.target_date)

        self.fetch_button = QPushButton("レース情報取得")
        self.fetch_button.clicked.connect(self.fetch_race_data)
        date_layout.addWidget(self.fetch_button)

        date_layout.addStretch()
        settings_layout.addLayout(date_layout)

        layout.addWidget(settings_group)

        # レース一覧
        race_group = QGroupBox("レース一覧")
        race_layout = QVBoxLayout()
        race_group.setLayout(race_layout)

        race_select_layout = QHBoxLayout()
        race_select_layout.addWidget(QLabel("競馬場:"))
        self.venue_combo = QComboBox()
        self.venue_combo.addItems(["全て", "東京", "中山", "京都", "阪神", "新潟", "中京", "小倉", "札幌", "函館", "福島"])
        self.venue_combo.currentTextChanged.connect(self.on_venue_changed)
        race_select_layout.addWidget(self.venue_combo)

        race_select_layout.addWidget(QLabel("レース:"))
        self.race_combo = QComboBox()
        self.race_combo.addItems(["レースを選択..."])
        race_select_layout.addWidget(self.race_combo)

        self.predict_button = QPushButton("予想実行")
        self.predict_button.clicked.connect(self.run_prediction)
        race_select_layout.addWidget(self.predict_button)

        race_select_layout.addStretch()
        race_layout.addLayout(race_select_layout)

        layout.addWidget(race_group)

        # 予想結果表示
        result_group = QGroupBox("予想結果")
        result_layout = QVBoxLayout()
        result_group.setLayout(result_layout)

        self.result_table = QTableWidget()
        self.result_table.setColumnCount(8)
        self.result_table.setHorizontalHeaderLabels([
            "予想順位", "馬番", "馬名", "騎手", "予測確率", "単勝オッズ", "人気", "推奨"
        ])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        result_layout.addWidget(self.result_table)

        # 推奨馬券
        recommendation_layout = QHBoxLayout()
        recommendation_layout.addWidget(QLabel("推奨馬券:"))
        self.recommendation_label = QLabel("---")
        self.recommendation_label.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #FF5722; padding: 5px;"
        )
        recommendation_layout.addWidget(self.recommendation_label)
        recommendation_layout.addStretch()
        result_layout.addLayout(recommendation_layout)

        layout.addWidget(result_group)

        # 操作ボタン
        action_layout = QHBoxLayout()

        self.save_button = QPushButton("予想を保存")
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.save_prediction)
        action_layout.addWidget(self.save_button)

        self.export_button = QPushButton("予想をエクスポート")
        self.export_button.setEnabled(False)
        action_layout.addWidget(self.export_button)

        action_layout.addStretch()
        layout.addLayout(action_layout)

        # ログ表示
        log_group = QGroupBox("実行ログ")
        log_layout = QVBoxLayout()
        log_group.setLayout(log_layout)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(120)
        log_layout.addWidget(self.log_text)

        layout.addWidget(log_group)

    def fetch_race_data(self):
        """レース情報を取得"""
        self.add_log("レース情報を取得しています...")

        target_date = self.target_date.date().toString("yyyy-MM-dd")
        self.add_log(f"対象日: {target_date}")

        # TODO: レース情報取得の実装
        self.add_log("※ レース情報取得機能は次のフェーズで実装されます")
        self.add_log("  src/scraper/ モジュールを実装後に有効化されます")

    def on_venue_changed(self, venue: str):
        """競馬場変更時の処理"""
        self.add_log(f"競馬場選択: {venue}")
        # TODO: 選択された競馬場のレース一覧を更新

    def run_prediction(self):
        """予想を実行"""
        self.add_log("予想を実行しています...")

        model = self.model_combo.currentText()
        race = self.race_combo.currentText()

        if model == "モデルファイルを選択...":
            self.add_log("エラー: モデルを選択してください")
            return

        if race == "レースを選択...":
            self.add_log("エラー: レースを選択してください")
            return

        self.add_log(f"モデル: {model}")
        self.add_log(f"レース: {race}")
        self.add_log("=" * 50)

        # TODO: 予想実行の実装
        self.add_log("※ 予想実行機能は次のフェーズで実装されます")
        self.add_log("  src/ml/ モジュールを実装後に有効化されます")

        # ダミーデータの表示
        self.result_table.setRowCount(3)

        dummy_data = [
            ["1", "5", "サンプルホース1", "騎手A", "0.35", "3.2", "1", "◎"],
            ["2", "3", "サンプルホース2", "騎手B", "0.28", "5.8", "3", "○"],
            ["3", "7", "サンプルホース3", "騎手C", "0.22", "8.5", "5", "▲"],
        ]

        for row_idx, row_data in enumerate(dummy_data):
            for col_idx, value in enumerate(row_data):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.result_table.setItem(row_idx, col_idx, item)

        self.recommendation_label.setText("3連単: 5-3-7 (推奨)")

        self.save_button.setEnabled(True)
        self.export_button.setEnabled(True)

        self.add_log("予想が完了しました")

    def save_prediction(self):
        """予想結果を保存"""
        self.add_log("予想結果をデータベースに保存しています...")
        # TODO: データベースへの保存処理
        self.add_log("保存しました")

    def add_log(self, message: str):
        """ログにメッセージを追加"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
