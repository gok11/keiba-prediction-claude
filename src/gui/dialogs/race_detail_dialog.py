"""
レース詳細ダイアログ
レースの詳細情報をタブ形式で表示
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QTableWidget, QTableWidgetItem, QTextEdit, QPushButton,
    QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt
from src.database.db_manager import DatabaseManager


class RaceDetailDialog(QDialog):
    """レース詳細ダイアログ"""

    def __init__(self, race_id: str, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.race_id = race_id
        self.db_manager = db_manager
        self.setWindowTitle(f"レース詳細: {race_id}")
        self.setMinimumSize(1000, 700)
        self.init_ui()

    def init_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout()

        # タブウィジェット
        self.tabs = QTabWidget()

        # 各タブを作成
        self.tabs.addTab(self.create_basic_info_tab(), "基本情報")
        self.tabs.addTab(self.create_results_tab(), "レース結果")
        self.tabs.addTab(self.create_payouts_tab(), "払戻金")
        self.tabs.addTab(self.create_lap_times_tab(), "ラップタイム")
        self.tabs.addTab(self.create_premium_info_tab(), "プレミアム情報")

        layout.addWidget(self.tabs)

        # 閉じるボタン
        close_button = QPushButton("閉じる")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

        self.setLayout(layout)

    def create_basic_info_tab(self):
        """基本情報タブ"""
        widget = QWidget()
        layout = QVBoxLayout()

        # レース情報を取得
        query = """
        SELECT race_name, date, venue, race_number, distance, track_type, track_condition,
               weather, race_class, grade, prize_money, track_index, track_comment,
               race_analysis_comment
        FROM races WHERE race_id = ?
        """
        race = self.db_manager.execute_query(query, (self.race_id,))

        if race:
            race = race[0]
            info_text = f"""
<h2>{race[0] if race[0] else ''}</h2>
<table border="0" cellpadding="5">
<tr><td><b>開催日:</b></td><td>{race[1] if race[1] else ''}</td></tr>
<tr><td><b>競馬場:</b></td><td>{race[2] if race[2] else ''} {race[3]}R</td></tr>
<tr><td><b>距離:</b></td><td>{race[4]}m {race[5] if race[5] else ''} {race[6] if race[6] else ''}</td></tr>
<tr><td><b>天気:</b></td><td>{race[7] if race[7] else ''}</td></tr>
<tr><td><b>クラス:</b></td><td>{race[8] if race[8] else ''}</td></tr>
"""
            if race[9]:
                info_text += f"<tr><td><b>グレード:</b></td><td>{race[9]}</td></tr>"
            if race[10]:
                info_text += f"<tr><td><b>賞金:</b></td><td>{race[10]:,}円</td></tr>"
            if race[11] is not None:
                info_text += f"<tr><td><b>馬場指数:</b></td><td>{race[11]}</td></tr>"

            info_text += "</table>"

            info_label = QLabel(info_text)
            info_label.setTextFormat(Qt.TextFormat.RichText)
            info_label.setWordWrap(True)
            layout.addWidget(info_label)

            # 馬場コメント
            if race[12]:
                layout.addWidget(QLabel("<b>馬場コメント:</b>"))
                track_comment = QTextEdit()
                track_comment.setPlainText(race[12])
                track_comment.setReadOnly(True)
                track_comment.setMaximumHeight(100)
                layout.addWidget(track_comment)

            # レース分析
            if race[13]:
                layout.addWidget(QLabel("<b>レース分析:</b>"))
                race_analysis = QTextEdit()
                race_analysis.setPlainText(race[13])
                race_analysis.setReadOnly(True)
                race_analysis.setMaximumHeight(100)
                layout.addWidget(race_analysis)

        else:
            layout.addWidget(QLabel("レース情報が見つかりませんでした"))

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_results_tab(self):
        """レース結果タブ"""
        widget = QWidget()
        layout = QVBoxLayout()

        # レース結果を取得
        query = """
        SELECT rr.finishing_position, rr.bracket_number, rr.horse_number, h.horse_name,
               rr.jockey_name, rr.trainer_name, rr.time, rr.margin, rr.odds_win,
               rr.popularity, rr.horse_weight, rr.horse_weight_diff, rr.last_3f,
               rr.time_index, rr.remarks, rr.horse_id
        FROM race_results rr
        LEFT JOIN horses h ON rr.horse_id = h.horse_id
        WHERE rr.race_id = ?
        ORDER BY rr.finishing_position
        """
        results = self.db_manager.execute_query(query, (self.race_id,))

        if results:
            table = QTableWidget()
            table.setColumnCount(14)
            table.setHorizontalHeaderLabels([
                "着順", "枠", "馬番", "馬名", "騎手", "調教師", "タイム", "着差",
                "人気", "オッズ", "馬体重", "上り", "指数", "備考"
            ])

            table.setRowCount(len(results))
            table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

            for row_idx, row_data in enumerate(results):
                pos = str(row_data[0]) if row_data[0] else ""
                bracket = str(row_data[1]) if row_data[1] else ""
                horse_num = str(row_data[2]) if row_data[2] else ""
                horse_name = row_data[3] if row_data[3] else ""
                jockey = row_data[4] if row_data[4] else ""
                trainer = row_data[5] if row_data[5] else ""
                time = row_data[6] if row_data[6] else ""
                margin = row_data[7] if row_data[7] else ""
                odds = f"{row_data[8]:.1f}" if row_data[8] else ""
                pop = str(row_data[9]) if row_data[9] else ""
                weight = f"{row_data[10]}({row_data[11]:+d})" if row_data[10] else ""
                last_3f = str(row_data[12]) if row_data[12] else ""
                time_idx = str(row_data[13]) if row_data[13] else ""
                remarks = row_data[14] if row_data[14] else ""
                horse_id = row_data[15]

                # 馬名にhorse_idを保存
                horse_name_item = QTableWidgetItem(horse_name)
                horse_name_item.setData(Qt.ItemDataRole.UserRole, horse_id)
                horse_name_item.setForeground(Qt.GlobalColor.blue)
                horse_name_item.setToolTip("ダブルクリックで過去成績を表示")

                table.setItem(row_idx, 0, QTableWidgetItem(pos))
                table.setItem(row_idx, 1, QTableWidgetItem(bracket))
                table.setItem(row_idx, 2, QTableWidgetItem(horse_num))
                table.setItem(row_idx, 3, horse_name_item)
                table.setItem(row_idx, 4, QTableWidgetItem(jockey))
                table.setItem(row_idx, 5, QTableWidgetItem(trainer))
                table.setItem(row_idx, 6, QTableWidgetItem(time))
                table.setItem(row_idx, 7, QTableWidgetItem(margin))
                table.setItem(row_idx, 8, QTableWidgetItem(pop))
                table.setItem(row_idx, 9, QTableWidgetItem(odds))
                table.setItem(row_idx, 10, QTableWidgetItem(weight))
                table.setItem(row_idx, 11, QTableWidgetItem(last_3f))
                table.setItem(row_idx, 12, QTableWidgetItem(time_idx))
                table.setItem(row_idx, 13, QTableWidgetItem(remarks))

            # 列幅の調整
            header = table.horizontalHeader()
            for i in range(14):
                if i == 3:  # 馬名
                    header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
                else:
                    header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

            # ダブルクリックで馬の詳細を表示
            table.doubleClicked.connect(lambda: self.show_horse_detail(table))

            layout.addWidget(table)
        else:
            layout.addWidget(QLabel("レース結果が見つかりませんでした"))

        widget.setLayout(layout)
        return widget

    def create_payouts_tab(self):
        """払戻金タブ"""
        widget = QWidget()
        layout = QVBoxLayout()

        # 払戻金を取得
        query = """
        SELECT payout_type, combination, payout, popularity
        FROM payouts
        WHERE race_id = ?
        ORDER BY
            CASE payout_type
                WHEN '単勝' THEN 1
                WHEN '複勝' THEN 2
                WHEN '枠連' THEN 3
                WHEN '馬連' THEN 4
                WHEN 'ワイド' THEN 5
                WHEN '馬単' THEN 6
                WHEN '3連複' THEN 7
                WHEN '3連単' THEN 8
            END,
            popularity
        """
        payouts = self.db_manager.execute_query(query, (self.race_id,))

        if payouts:
            table = QTableWidget()
            table.setColumnCount(4)
            table.setHorizontalHeaderLabels(["券種", "組み合わせ", "払戻金", "人気"])
            table.setRowCount(len(payouts))
            table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

            for row_idx, row_data in enumerate(payouts):
                payout_type = row_data[0]
                combination = row_data[1]
                payout = f"{row_data[2]:,}円" if row_data[2] else ""
                pop = f"{row_data[3]}番人気" if row_data[3] else ""

                table.setItem(row_idx, 0, QTableWidgetItem(payout_type))
                table.setItem(row_idx, 1, QTableWidgetItem(combination))
                table.setItem(row_idx, 2, QTableWidgetItem(payout))
                table.setItem(row_idx, 3, QTableWidgetItem(pop))

            # 列幅の調整
            header = table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

            layout.addWidget(table)
        else:
            layout.addWidget(QLabel("払戻金情報が見つかりませんでした"))

        widget.setLayout(layout)
        return widget

    def create_lap_times_tab(self):
        """ラップタイムタブ"""
        widget = QWidget()
        layout = QVBoxLayout()

        # ラップタイムを取得
        query = """
        SELECT section, lap_time, pace
        FROM lap_times
        WHERE race_id = ?
        ORDER BY section
        """
        laps = self.db_manager.execute_query(query, (self.race_id,))

        if laps:
            # テキスト表示
            lap_str = " - ".join([f"{lap[1]:.1f}" for lap in laps])
            total_time = sum([lap[1] for lap in laps])

            info_label = QLabel(f"<b>ラップタイム:</b> {lap_str}<br><b>合計:</b> {total_time:.1f}秒")
            info_label.setTextFormat(Qt.TextFormat.RichText)
            layout.addWidget(info_label)

            # テーブル表示
            table = QTableWidget()
            table.setColumnCount(3)
            table.setHorizontalHeaderLabels(["区間", "タイム(秒)", "ペース"])
            table.setRowCount(len(laps))
            table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

            for row_idx, row_data in enumerate(laps):
                section = f"{(row_data[0]-1)*200}-{row_data[0]*200}m"
                lap_time = f"{row_data[1]:.1f}"
                pace = row_data[2] if row_data[2] else ""

                table.setItem(row_idx, 0, QTableWidgetItem(section))
                table.setItem(row_idx, 1, QTableWidgetItem(lap_time))
                table.setItem(row_idx, 2, QTableWidgetItem(pace))

            # 列幅の調整
            header = table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

            layout.addWidget(table)
        else:
            layout.addWidget(QLabel("ラップタイム情報が見つかりませんでした"))

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_premium_info_tab(self):
        """プレミアム情報タブ（短評含む）"""
        widget = QWidget()
        layout = QVBoxLayout()

        # 注目馬短評を取得
        query = """
        SELECT finishing_position, horse_name, review
        FROM horse_short_reviews
        WHERE race_id = ?
        ORDER BY finishing_position
        """
        reviews = self.db_manager.execute_query(query, (self.race_id,))

        if reviews:
            layout.addWidget(QLabel("<h3>注目馬短評</h3>"))

            for row_data in reviews:
                pos = f"{row_data[0]}着" if row_data[0] else "---"
                horse_name = row_data[1]
                review = row_data[2]

                # 馬名と着順
                header = QLabel(f"<b>{pos}: {horse_name}</b>")
                header.setTextFormat(Qt.TextFormat.RichText)
                layout.addWidget(header)

                # 短評
                review_text = QTextEdit()
                review_text.setPlainText(review)
                review_text.setReadOnly(True)
                review_text.setMaximumHeight(80)
                layout.addWidget(review_text)

        else:
            layout.addWidget(QLabel("プレミアム情報が見つかりませんでした"))

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def show_horse_detail(self, table):
        """馬の詳細を表示"""
        current_row = table.currentRow()
        if current_row < 0:
            return

        # 馬名列（3列目）からhorse_idを取得
        horse_item = table.item(current_row, 3)
        if not horse_item:
            return

        horse_id = horse_item.data(Qt.ItemDataRole.UserRole)
        if not horse_id:
            QMessageBox.warning(self, "警告", "馬IDが取得できませんでした")
            return

        # 馬の詳細ダイアログを表示
        from src.gui.dialogs.horse_history_dialog import HorseHistoryDialog
        dialog = HorseHistoryDialog(horse_id, self.db_manager, self)
        dialog.exec()
