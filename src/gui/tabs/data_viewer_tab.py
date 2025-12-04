"""
データ閲覧タブ
レース一覧を表示し、詳細を閲覧できる機能を提供
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QDateEdit, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt, QDate
from datetime import datetime, timedelta
from src.database.db_manager import DatabaseManager
from src.utils.config import app_config
from src.gui.dialogs.race_detail_dialog import RaceDetailDialog


class DataViewerTab(QWidget):
    """データ閲覧タブ"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = DatabaseManager(app_config.get('database.path', 'data/keiba.db'))
        self.db_manager.connect()
        self.init_ui()
        self.load_races()

    def init_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout()

        # タイトル
        title = QLabel("データ閲覧")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # 期間フィルタ
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("期間:"))

        # デフォルトは過去30日間
        end_date = QDate.currentDate()
        start_date = end_date.addDays(-30)

        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(start_date)
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        filter_layout.addWidget(self.start_date_edit)

        filter_layout.addWidget(QLabel("～"))

        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(end_date)
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")
        filter_layout.addWidget(self.end_date_edit)

        self.search_button = QPushButton("検索")
        self.search_button.clicked.connect(self.load_races)
        filter_layout.addWidget(self.search_button)

        self.stats_button = QPushButton("統計情報")
        self.stats_button.clicked.connect(self.show_stats)
        filter_layout.addWidget(self.stats_button)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # レース一覧テーブル
        self.race_table = QTableWidget()
        self.race_table.setColumnCount(9)
        self.race_table.setHorizontalHeaderLabels([
            "日付", "競馬場", "R", "レース名", "グレード", "距離", "馬場", "天気", "クラス"
        ])

        # テーブルの設定
        self.race_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.race_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.race_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.race_table.setSortingEnabled(True)

        # 列幅の調整
        header = self.race_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # 日付
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # 競馬場
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # R
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # レース名
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # グレード
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # 距離
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # 馬場
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # 天気
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)  # クラス

        # ダブルクリックで詳細表示
        self.race_table.doubleClicked.connect(self.show_race_detail)

        layout.addWidget(self.race_table)

        # 件数表示
        self.count_label = QLabel()
        layout.addWidget(self.count_label)

        # ボタン
        button_layout = QHBoxLayout()

        self.detail_button = QPushButton("詳細表示")
        self.detail_button.clicked.connect(self.show_race_detail)
        button_layout.addWidget(self.detail_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_races(self):
        """レース一覧を読み込み"""
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")

        query = """
        SELECT race_id, date, venue, race_number, race_name, grade, distance,
               track_type, track_condition, weather, race_class
        FROM races
        WHERE date BETWEEN ? AND ?
        ORDER BY date DESC, venue, race_number
        LIMIT 1000
        """

        try:
            results = self.db_manager.execute_query(query, (start_date, end_date))

            # テーブルをクリア
            self.race_table.setRowCount(0)
            self.race_table.setSortingEnabled(False)

            # データを追加
            for row_data in results:
                row = self.race_table.rowCount()
                self.race_table.insertRow(row)

                race_id = row_data[0]
                date = row_data[1] if row_data[1] else ""
                venue = row_data[2] if row_data[2] else ""
                race_num = str(row_data[3]) if row_data[3] else ""
                race_name = row_data[4] if row_data[4] else ""
                grade = row_data[5] if row_data[5] else ""
                distance = f"{row_data[6]}m" if row_data[6] else ""
                track = f"{row_data[7]}{row_data[8]}" if (row_data[7] and row_data[8]) else ""
                weather = row_data[9] if row_data[9] else ""
                race_class = row_data[10] if row_data[10] else ""

                # race_idは非表示だが、データとして保持
                item = QTableWidgetItem(date)
                item.setData(Qt.ItemDataRole.UserRole, race_id)
                self.race_table.setItem(row, 0, item)

                self.race_table.setItem(row, 1, QTableWidgetItem(venue))
                self.race_table.setItem(row, 2, QTableWidgetItem(race_num))
                self.race_table.setItem(row, 3, QTableWidgetItem(race_name))
                self.race_table.setItem(row, 4, QTableWidgetItem(grade))
                self.race_table.setItem(row, 5, QTableWidgetItem(distance))
                self.race_table.setItem(row, 6, QTableWidgetItem(track))
                self.race_table.setItem(row, 7, QTableWidgetItem(weather))
                self.race_table.setItem(row, 8, QTableWidgetItem(race_class))

            self.race_table.setSortingEnabled(True)
            self.count_label.setText(f"合計: {len(results)} 件")

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"データの読み込みに失敗しました:\n{e}")

    def show_race_detail(self):
        """レース詳細を表示"""
        current_row = self.race_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "レースを選択してください")
            return

        # race_idを取得
        race_id = self.race_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)

        # 詳細ダイアログを表示
        dialog = RaceDetailDialog(race_id, self.db_manager, self)
        dialog.exec()

    def show_stats(self):
        """統計情報を表示"""
        try:
            # データベース統計を取得
            stats_info = []

            tables = [
                ('races', 'レース数'),
                ('horses', '馬数'),
                ('race_results', 'レース結果数'),
                ('payouts', '払戻金記録数'),
                ('lap_times', 'ラップタイム記録数'),
                ('training_details', '調教タイム記録数'),
                ('stable_comments', '厩舎コメント数'),
                ('horse_short_reviews', '注目馬短評数'),
            ]

            for table_name, description in tables:
                try:
                    count_query = f"SELECT COUNT(*) FROM {table_name}"
                    result = self.db_manager.execute_query(count_query)
                    count = result[0][0] if result else 0
                    stats_info.append(f"{description}: {count:,} 件")
                except Exception:
                    stats_info.append(f"{description}: エラー")

            # データ期間
            date_query = "SELECT MIN(date) as oldest, MAX(date) as newest FROM races"
            result = self.db_manager.execute_query(date_query)
            if result and result[0][0]:
                oldest = result[0][0]
                newest = result[0][1]
                stats_info.append(f"\nデータ期間: {oldest} ～ {newest}")

            # 競馬場別レース数
            venue_query = """
            SELECT venue, COUNT(*) as count
            FROM races
            GROUP BY venue
            ORDER BY count DESC
            """
            venues = self.db_manager.execute_query(venue_query)
            if venues:
                stats_info.append("\n【競馬場別レース数】")
                for row in venues:
                    stats_info.append(f"  {row[0]}: {row[1]:,} レース")

            QMessageBox.information(
                self,
                "データベース統計情報",
                "\n".join(stats_info)
            )

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"統計情報の取得に失敗しました:\n{e}")

    def closeEvent(self, event):
        """タブが閉じられる時"""
        if self.db_manager:
            self.db_manager.disconnect()
        event.accept()
