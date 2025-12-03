"""
バックテストタブ
過去データを使用してモデルの性能を検証するUI
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QComboBox, QSpinBox,
    QDoubleSpinBox, QProgressBar, QTextEdit,
    QDateEdit, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PyQt6.QtCore import QDate
from datetime import datetime


class BacktestTab(QWidget):
    """バックテストタブ"""

    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.init_ui()

    def init_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # モデル選択グループ
        model_group = QGroupBox("モデル設定")
        model_layout = QHBoxLayout()
        model_group.setLayout(model_layout)

        model_layout.addWidget(QLabel("使用モデル:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["モデルファイルを選択..."])
        # TODO: 訓練済みモデルのリストを読み込む
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()

        layout.addWidget(model_group)

        # バックテスト期間設定
        period_group = QGroupBox("バックテスト期間")
        period_layout = QHBoxLayout()
        period_group.setLayout(period_layout)

        period_layout.addWidget(QLabel("開始日:"))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate(2023, 1, 1))
        self.start_date.setCalendarPopup(True)
        period_layout.addWidget(self.start_date)

        period_layout.addWidget(QLabel("終了日:"))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        period_layout.addWidget(self.end_date)

        period_layout.addStretch()

        layout.addWidget(period_group)

        # 購入戦略設定
        strategy_group = QGroupBox("購入戦略")
        strategy_layout = QVBoxLayout()
        strategy_group.setLayout(strategy_layout)

        # 賭け式選択
        bet_type_layout = QHBoxLayout()
        bet_type_layout.addWidget(QLabel("賭け式:"))
        self.bet_type_combo = QComboBox()
        self.bet_type_combo.addItems([
            "単勝", "複勝", "馬連", "馬単", "ワイド", "3連複", "3連単"
        ])
        bet_type_layout.addWidget(self.bet_type_combo)
        bet_type_layout.addStretch()
        strategy_layout.addLayout(bet_type_layout)

        # 購入条件
        condition_layout = QHBoxLayout()
        condition_layout.addWidget(QLabel("購入条件:"))
        self.condition_combo = QComboBox()
        self.condition_combo.addItems([
            "予測確率上位N頭", "予測確率閾値以上", "全て購入"
        ])
        condition_layout.addWidget(self.condition_combo)

        self.condition_value = QSpinBox()
        self.condition_value.setRange(1, 18)
        self.condition_value.setValue(3)
        condition_layout.addWidget(self.condition_value)
        condition_layout.addStretch()
        strategy_layout.addLayout(condition_layout)

        # 賭け金額
        amount_layout = QHBoxLayout()
        amount_layout.addWidget(QLabel("賭け金額:"))
        self.bet_amount = QSpinBox()
        self.bet_amount.setRange(100, 100000)
        self.bet_amount.setValue(100)
        self.bet_amount.setSuffix(" 円")
        amount_layout.addWidget(self.bet_amount)
        amount_layout.addStretch()
        strategy_layout.addLayout(amount_layout)

        layout.addWidget(strategy_group)

        # コントロールボタン
        control_layout = QHBoxLayout()

        self.run_button = QPushButton("バックテスト実行")
        self.run_button.clicked.connect(self.run_backtest)
        control_layout.addWidget(self.run_button)

        self.export_button = QPushButton("結果をエクスポート")
        self.export_button.setEnabled(False)
        control_layout.addWidget(self.export_button)

        control_layout.addStretch()
        layout.addLayout(control_layout)

        # プログレスバー
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # 結果表示グループ
        result_group = QGroupBox("バックテスト結果")
        result_layout = QVBoxLayout()
        result_group.setLayout(result_layout)

        # サマリー表示
        summary_layout = QHBoxLayout()

        self.roi_label = QLabel("ROI: ---")
        self.roi_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2196F3;")
        summary_layout.addWidget(self.roi_label)

        self.hit_rate_label = QLabel("的中率: ---")
        self.hit_rate_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4CAF50;")
        summary_layout.addWidget(self.hit_rate_label)

        self.total_profit_label = QLabel("総収支: ---")
        self.total_profit_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #FF9800;")
        summary_layout.addWidget(self.total_profit_label)

        summary_layout.addStretch()
        result_layout.addLayout(summary_layout)

        # 詳細結果テーブル
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(7)
        self.result_table.setHorizontalHeaderLabels([
            "日付", "レース名", "購入", "的中", "払戻", "収支", "ROI"
        ])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        result_layout.addWidget(self.result_table)

        layout.addWidget(result_group)

        # ログ表示
        log_group = QGroupBox("実行ログ")
        log_layout = QVBoxLayout()
        log_group.setLayout(log_layout)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)

        layout.addWidget(log_group)

    def run_backtest(self):
        """バックテストを実行"""
        self.run_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.log_text.clear()

        self.add_log("バックテストを開始します...")

        # 設定の取得
        config = {
            'model': self.model_combo.currentText(),
            'start_date': self.start_date.date().toString("yyyy-MM-dd"),
            'end_date': self.end_date.date().toString("yyyy-MM-dd"),
            'bet_type': self.bet_type_combo.currentText(),
            'condition': self.condition_combo.currentText(),
            'condition_value': self.condition_value.value(),
            'bet_amount': self.bet_amount.value()
        }

        self.add_log(f"期間: {config['start_date']} ～ {config['end_date']}")
        self.add_log(f"賭け式: {config['bet_type']}")
        self.add_log(f"購入条件: {config['condition']} ({config['condition_value']})")
        self.add_log("=" * 50)

        # TODO: バックテスト処理の実装
        self.add_log("※ バックテスト機能は次のフェーズで実装されます")
        self.add_log("  src/backtest/ モジュールを実装後に有効化されます")

        # ダミーデータの表示
        self.roi_label.setText("ROI: 105.2%")
        self.hit_rate_label.setText("的中率: 28.5%")
        self.total_profit_label.setText("総収支: +52,000円")

        self.progress_bar.setValue(100)
        self.run_button.setEnabled(True)
        self.export_button.setEnabled(True)

    def add_log(self, message: str):
        """ログにメッセージを追加"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
