"""
馬の過去成績ダイアログ
馬の基本情報と過去の出走履歴を表示
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QTextEdit, QScrollArea, QWidget
)
from PyQt6.QtCore import Qt
from src.database.db_manager import DatabaseManager


class HorseHistoryDialog(QDialog):
    """馬の過去成績ダイアログ"""

    def __init__(self, horse_id: str, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.horse_id = horse_id
        self.db_manager = db_manager
        self.setWindowTitle(f"馬の詳細: {horse_id}")
        self.setMinimumSize(1100, 600)
        self.init_ui()

    def init_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout()

        # 馬の基本情報を取得
        horse_query = """
        SELECT horse_name, birth_date, sex, sire, dam, damsire
        FROM horses WHERE horse_id = ?
        """
        horse = self.db_manager.execute_query(horse_query, (self.horse_id,))

        if horse:
            horse = horse[0]
            horse_name = horse[0] if horse[0] else "---"
            birth_date = horse[1] if horse[1] else "---"
            sex = horse[2] if horse[2] else "---"
            sire = horse[3] if horse[3] else "---"
            dam = horse[4] if horse[4] else "---"
            damsire = horse[5] if horse[5] else "---"

            # 基本情報
            info_html = f"""
<h2>{horse_name}</h2>
<table border="0" cellpadding="5">
<tr><td><b>馬ID:</b></td><td>{self.horse_id}</td></tr>
<tr><td><b>生年月日:</b></td><td>{birth_date}</td></tr>
<tr><td><b>性別:</b></td><td>{sex}</td></tr>
<tr><td><b>父:</b></td><td>{sire}</td></tr>
<tr><td><b>母:</b></td><td>{dam}</td></tr>
<tr><td><b>母父:</b></td><td>{damsire}</td></tr>
</table>
"""
            info_label = QLabel(info_html)
            info_label.setTextFormat(Qt.TextFormat.RichText)
            info_label.setWordWrap(True)
            layout.addWidget(info_label)

        else:
            layout.addWidget(QLabel("馬情報が見つかりませんでした"))

        # 過去成績
        layout.addWidget(QLabel("<h3>過去成績</h3>"))

        history_query = """
        SELECT r.date, r.venue, r.race_name, r.distance, r.track_type, r.track_condition,
               rr.finishing_position, rr.time, rr.jockey_name, rr.popularity, rr.odds_win,
               rr.horse_weight, rr.horse_weight_diff, r.race_id
        FROM race_results rr
        LEFT JOIN races r ON rr.race_id = r.race_id
        WHERE rr.horse_id = ?
        ORDER BY r.date DESC
        LIMIT 50
        """
        history = self.db_manager.execute_query(history_query, (self.horse_id,))

        if history:
            table = QTableWidget()
            table.setColumnCount(13)
            table.setHorizontalHeaderLabels([
                "日付", "競馬場", "レース名", "距離", "馬場", "着順",
                "タイム", "騎手", "人気", "オッズ", "馬体重", "増減", "馬場状態"
            ])

            table.setRowCount(len(history))
            table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

            for row_idx, row_data in enumerate(history):
                date = row_data[0] if row_data[0] else ""
                venue = row_data[1] if row_data[1] else ""
                race_name = row_data[2][:20] if row_data[2] else ""  # 長いレース名は切り詰め
                distance = f"{row_data[3]}m" if row_data[3] else ""
                track = row_data[4] if row_data[4] else ""
                pos = str(row_data[6]) if row_data[6] else ""
                time = str(row_data[7]) if row_data[7] else ""
                jockey = row_data[8] if row_data[8] else ""
                pop = str(row_data[9]) if row_data[9] else ""
                odds = f"{row_data[10]:.1f}" if row_data[10] else ""
                weight = str(row_data[11]) if row_data[11] else ""
                weight_diff = f"{row_data[12]:+d}" if row_data[12] is not None else ""
                condition = row_data[5] if row_data[5] else ""
                race_id = row_data[13]

                # 日付にrace_idを保存（レース詳細へのリンク用）
                date_item = QTableWidgetItem(date)
                date_item.setData(Qt.ItemDataRole.UserRole, race_id)
                date_item.setForeground(Qt.GlobalColor.blue)
                date_item.setToolTip("ダブルクリックでレース詳細を表示")

                table.setItem(row_idx, 0, date_item)
                table.setItem(row_idx, 1, QTableWidgetItem(venue))
                table.setItem(row_idx, 2, QTableWidgetItem(race_name))
                table.setItem(row_idx, 3, QTableWidgetItem(distance))
                table.setItem(row_idx, 4, QTableWidgetItem(track))
                table.setItem(row_idx, 5, QTableWidgetItem(pos))
                table.setItem(row_idx, 6, QTableWidgetItem(time))
                table.setItem(row_idx, 7, QTableWidgetItem(jockey))
                table.setItem(row_idx, 8, QTableWidgetItem(pop))
                table.setItem(row_idx, 9, QTableWidgetItem(odds))
                table.setItem(row_idx, 10, QTableWidgetItem(weight))
                table.setItem(row_idx, 11, QTableWidgetItem(weight_diff))
                table.setItem(row_idx, 12, QTableWidgetItem(condition))

            # 列幅の調整
            header = table.horizontalHeader()
            for i in range(13):
                if i == 2:  # レース名
                    header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
                else:
                    header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

            # ダブルクリックでレース詳細を表示
            table.doubleClicked.connect(lambda: self.show_race_detail(table))

            layout.addWidget(table)

            # 統計情報
            stats_label = QLabel(f"<b>合計:</b> {len(history)} 戦")
            stats_label.setTextFormat(Qt.TextFormat.RichText)
            layout.addWidget(stats_label)

        else:
            layout.addWidget(QLabel("過去成績が見つかりませんでした"))

        # 厩舎コメントを取得
        comment_query = """
        SELECT sc.created_at, sc.comment
        FROM stable_comments sc
        WHERE sc.horse_id = ?
        ORDER BY sc.created_at DESC
        LIMIT 5
        """
        comments = self.db_manager.execute_query(comment_query, (self.horse_id,))

        if comments:
            layout.addWidget(QLabel("<h3>厩舎コメント（最新5件）</h3>"))

            for row_data in comments:
                comment_date = row_data[0] if row_data[0] else ""
                comment = row_data[1] if row_data[1] else ""

                date_label = QLabel(f"<b>{comment_date}</b>")
                date_label.setTextFormat(Qt.TextFormat.RichText)
                layout.addWidget(date_label)

                comment_text = QTextEdit()
                comment_text.setPlainText(comment)
                comment_text.setReadOnly(True)
                comment_text.setMaximumHeight(60)
                layout.addWidget(comment_text)

        # 閉じるボタン
        close_button = QPushButton("閉じる")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

        self.setLayout(layout)

    def show_race_detail(self, table):
        """レース詳細を表示"""
        current_row = table.currentRow()
        if current_row < 0:
            return

        # 日付列（0列目）からrace_idを取得
        date_item = table.item(current_row, 0)
        if not date_item:
            return

        race_id = date_item.data(Qt.ItemDataRole.UserRole)
        if not race_id:
            return

        # レース詳細ダイアログを表示
        from src.gui.dialogs.race_detail_dialog import RaceDetailDialog
        dialog = RaceDetailDialog(race_id, self.db_manager, self)
        dialog.exec()
