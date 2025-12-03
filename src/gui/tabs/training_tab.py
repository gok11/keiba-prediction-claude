"""
トレーニングタブ
機械学習モデルの訓練を行うUI
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QComboBox, QSpinBox,
    QDoubleSpinBox, QProgressBar, QTextEdit,
    QCheckBox, QMessageBox
)
from datetime import datetime


class TrainingTab(QWidget):
    """トレーニングタブ"""

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
        model_layout = QVBoxLayout()
        model_group.setLayout(model_layout)

        # モデル選択
        model_select_layout = QHBoxLayout()
        model_select_layout.addWidget(QLabel("モデル:"))

        self.model_combo = QComboBox()
        self.model_combo.addItems(["LightGBM", "XGBoost", "RandomForest"])
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        model_select_layout.addWidget(self.model_combo)
        model_select_layout.addStretch()
        model_layout.addLayout(model_select_layout)

        # 予測対象選択
        target_layout = QHBoxLayout()
        target_layout.addWidget(QLabel("予測対象:"))

        self.target_combo = QComboBox()
        self.target_combo.addItems(["着順（1-3着）", "勝率", "複勝率"])
        target_layout.addWidget(self.target_combo)
        target_layout.addStretch()
        model_layout.addLayout(target_layout)

        layout.addWidget(model_group)

        # ハイパーパラメータグループ
        param_group = QGroupBox("ハイパーパラメータ")
        param_layout = QVBoxLayout()
        param_group.setLayout(param_layout)

        # 学習率
        lr_layout = QHBoxLayout()
        lr_layout.addWidget(QLabel("学習率:"))
        self.learning_rate = QDoubleSpinBox()
        self.learning_rate.setRange(0.001, 1.0)
        self.learning_rate.setValue(0.1)
        self.learning_rate.setDecimals(3)
        self.learning_rate.setSingleStep(0.01)
        lr_layout.addWidget(self.learning_rate)
        lr_layout.addStretch()
        param_layout.addLayout(lr_layout)

        # イテレーション数
        iter_layout = QHBoxLayout()
        iter_layout.addWidget(QLabel("イテレーション数:"))
        self.n_iterations = QSpinBox()
        self.n_iterations.setRange(10, 10000)
        self.n_iterations.setValue(100)
        iter_layout.addWidget(self.n_iterations)
        iter_layout.addStretch()
        param_layout.addLayout(iter_layout)

        # 木の深さ
        depth_layout = QHBoxLayout()
        depth_layout.addWidget(QLabel("木の深さ:"))
        self.max_depth = QSpinBox()
        self.max_depth.setRange(3, 20)
        self.max_depth.setValue(6)
        depth_layout.addWidget(self.max_depth)
        depth_layout.addStretch()
        param_layout.addLayout(depth_layout)

        layout.addWidget(param_group)

        # データ設定グループ
        data_group = QGroupBox("データ設定")
        data_layout = QVBoxLayout()
        data_group.setLayout(data_layout)

        # テストデータ分割比率
        split_layout = QHBoxLayout()
        split_layout.addWidget(QLabel("テストデータ比率:"))
        self.test_size = QDoubleSpinBox()
        self.test_size.setRange(0.1, 0.5)
        self.test_size.setValue(0.2)
        self.test_size.setSingleStep(0.05)
        self.test_size.setSuffix(" %")
        split_layout.addWidget(self.test_size)
        split_layout.addStretch()
        data_layout.addLayout(split_layout)

        # クロスバリデーション
        cv_layout = QHBoxLayout()
        self.cv_checkbox = QCheckBox("クロスバリデーション実行")
        self.cv_checkbox.setChecked(True)
        cv_layout.addWidget(self.cv_checkbox)

        self.cv_folds = QSpinBox()
        self.cv_folds.setRange(2, 10)
        self.cv_folds.setValue(5)
        cv_layout.addWidget(QLabel("分割数:"))
        cv_layout.addWidget(self.cv_folds)
        cv_layout.addStretch()
        data_layout.addLayout(cv_layout)

        layout.addWidget(data_group)

        # コントロールボタン
        control_layout = QHBoxLayout()

        self.train_button = QPushButton("トレーニング開始")
        self.train_button.clicked.connect(self.start_training)
        control_layout.addWidget(self.train_button)

        self.stop_button = QPushButton("中止")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_training)
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
        log_group = QGroupBox("トレーニングログ")
        log_layout = QVBoxLayout()
        log_group.setLayout(log_layout)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)

        layout.addWidget(log_group)

    def on_model_changed(self, model_name: str):
        """モデル変更時の処理"""
        self.add_log(f"モデル選択: {model_name}")

    def start_training(self):
        """トレーニングを開始"""
        self.train_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setValue(0)
        self.log_text.clear()

        self.add_log("トレーニングを開始します...")

        # 設定の取得
        config = {
            'model': self.model_combo.currentText(),
            'target': self.target_combo.currentText(),
            'learning_rate': self.learning_rate.value(),
            'n_iterations': self.n_iterations.value(),
            'max_depth': self.max_depth.value(),
            'test_size': self.test_size.value(),
            'cv_enabled': self.cv_checkbox.isChecked(),
            'cv_folds': self.cv_folds.value()
        }

        self.add_log(f"モデル: {config['model']}")
        self.add_log(f"予測対象: {config['target']}")
        self.add_log(f"学習率: {config['learning_rate']}")
        self.add_log(f"イテレーション数: {config['n_iterations']}")
        self.add_log("=" * 50)

        # TODO: トレーニング処理の実装
        self.add_log("※ トレーニング機能は次のフェーズで実装されます")
        self.add_log("  src/ml/ モジュールを実装後に有効化されます")

        self.progress_bar.setValue(100)
        self.progress_label.setText("準備完了（実装待ち）")

        self.train_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def stop_training(self):
        """トレーニングを中止"""
        self.add_log("トレーニングを中止しています...")
        self.train_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def add_log(self, message: str):
        """ログにメッセージを追加"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
