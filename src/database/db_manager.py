"""
データベース管理モジュール
SQLiteデータベースの初期化、接続、基本的なCRUD操作を提供
"""

import sqlite3
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd


class DatabaseManager:
    """データベース操作を管理するクラス"""

    def __init__(self, db_path: str = "data/keiba.db"):
        """
        Args:
            db_path: データベースファイルのパス
        """
        self.db_path = db_path
        self._ensure_db_directory()
        self.connection = None

    def _ensure_db_directory(self):
        """データベースディレクトリが存在することを確認"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        """データベースに接続"""
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # 辞書形式でアクセス可能に
            # データベースが初期化されていない場合は自動初期化
            self._auto_initialize_if_needed()
        return self.connection

    def _auto_initialize_if_needed(self):
        """データベースが未初期化の場合、自動的に初期化する"""
        cursor = self.connection.cursor()
        # racesテーブルの存在をチェック
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='races'")
        if cursor.fetchone() is None:
            print("データベースが初期化されていません。自動初期化を実行します...")
            self.initialize_database()

    def disconnect(self):
        """データベース接続を切断"""
        if self.connection:
            self.connection.close()
            self.connection = None

    def initialize_database(self):
        """スキーマファイルを使用してデータベースを初期化"""
        schema_path = Path(__file__).parent / "schema.sql"

        if not schema_path.exists():
            raise FileNotFoundError(f"スキーマファイルが見つかりません: {schema_path}")

        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        conn = self.connect()
        cursor = conn.cursor()

        # スキーマを実行（複数のSQL文を分割して実行）
        cursor.executescript(schema_sql)
        conn.commit()

        print(f"データベースを初期化しました: {self.db_path}")

    def execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """
        SELECTクエリを実行して結果を返す

        Args:
            query: SQLクエリ
            params: プレースホルダーのパラメータ

        Returns:
            クエリ結果のリスト
        """
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """
        INSERT/UPDATE/DELETEクエリを実行

        Args:
            query: SQLクエリ
            params: プレースホルダーのパラメータ

        Returns:
            影響を受けた行数
        """
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount

    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """
        複数行のINSERT/UPDATE/DELETEを一括実行

        Args:
            query: SQLクエリ
            params_list: パラメータのリスト

        Returns:
            影響を受けた行数
        """
        conn = self.connect()
        cursor = conn.cursor()
        cursor.executemany(query, params_list)
        conn.commit()
        return cursor.rowcount

    def query_to_dataframe(self, query: str, params: tuple = ()) -> pd.DataFrame:
        """
        クエリ結果をpandas DataFrameとして返す

        Args:
            query: SQLクエリ
            params: プレースホルダーのパラメータ

        Returns:
            クエリ結果のDataFrame
        """
        conn = self.connect()
        return pd.read_sql_query(query, conn, params=params)

    def insert_race(self, race_data: Dict[str, Any]) -> bool:
        """
        レース情報を挿入

        Args:
            race_data: レースデータの辞書

        Returns:
            成功したかどうか
        """
        query = """
        INSERT OR REPLACE INTO races
        (race_id, race_name, date, venue, distance, track_type, track_condition,
         weather, race_class, prize_money, grade, race_number, start_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            race_data.get('race_id'),
            race_data.get('race_name'),
            race_data.get('date'),
            race_data.get('venue'),
            race_data.get('distance'),
            race_data.get('track_type'),
            race_data.get('track_condition'),
            race_data.get('weather'),
            race_data.get('race_class'),
            race_data.get('prize_money'),
            race_data.get('grade'),
            race_data.get('race_number'),
            race_data.get('start_time')
        )
        try:
            self.execute_update(query, params)
            return True
        except Exception as e:
            print(f"レース挿入エラー: {e}")
            return False

    def insert_horse(self, horse_data: Dict[str, Any]) -> bool:
        """
        馬情報を挿入

        Args:
            horse_data: 馬データの辞書

        Returns:
            成功したかどうか
        """
        query = """
        INSERT OR REPLACE INTO horses
        (horse_id, horse_name, birth_date, sex, sire, dam, damsire, breeder, owner)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            horse_data.get('horse_id'),
            horse_data.get('horse_name'),
            horse_data.get('birth_date'),
            horse_data.get('sex'),
            horse_data.get('sire'),
            horse_data.get('dam'),
            horse_data.get('damsire'),
            horse_data.get('breeder'),
            horse_data.get('owner')
        )
        try:
            self.execute_update(query, params)
            return True
        except Exception as e:
            print(f"馬挿入エラー: {e}")
            return False

    def insert_race_result(self, result_data: Dict[str, Any]) -> bool:
        """
        レース結果を挿入

        Args:
            result_data: レース結果データの辞書

        Returns:
            成功したかどうか
        """
        query = """
        INSERT INTO race_results
        (race_id, horse_id, finishing_position, bracket_number, horse_number,
         jockey_id, jockey_name, jockey_weight, trainer_id, trainer_name,
         horse_weight, horse_weight_diff, odds_win, odds_place, popularity,
         time, margin, last_3f, passing_order, running_style, disqualification)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            result_data.get('race_id'),
            result_data.get('horse_id'),
            result_data.get('finishing_position'),
            result_data.get('bracket_number'),
            result_data.get('horse_number'),
            result_data.get('jockey_id'),
            result_data.get('jockey_name'),
            result_data.get('jockey_weight'),
            result_data.get('trainer_id'),
            result_data.get('trainer_name'),
            result_data.get('horse_weight'),
            result_data.get('horse_weight_diff'),
            result_data.get('odds_win'),
            result_data.get('odds_place'),
            result_data.get('popularity'),
            result_data.get('time'),
            result_data.get('margin'),
            result_data.get('last_3f'),
            result_data.get('passing_order'),
            result_data.get('running_style'),
            result_data.get('disqualification')
        )
        try:
            self.execute_update(query, params)
            return True
        except Exception as e:
            print(f"レース結果挿入エラー: {e}")
            return False

    def get_races_by_date_range(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        期間内のレース情報を取得

        Args:
            start_date: 開始日 (YYYY-MM-DD)
            end_date: 終了日 (YYYY-MM-DD)

        Returns:
            レース情報のDataFrame
        """
        query = """
        SELECT * FROM races
        WHERE date BETWEEN ? AND ?
        ORDER BY date, venue, race_number
        """
        return self.query_to_dataframe(query, (start_date, end_date))

    def get_race_results(self, race_id: str) -> pd.DataFrame:
        """
        特定レースの結果を取得

        Args:
            race_id: レースID

        Returns:
            レース結果のDataFrame
        """
        query = """
        SELECT rr.*, h.horse_name, h.sex, h.sire, h.dam
        FROM race_results rr
        LEFT JOIN horses h ON rr.horse_id = h.horse_id
        WHERE rr.race_id = ?
        ORDER BY rr.finishing_position
        """
        return self.query_to_dataframe(query, (race_id,))

    def get_horse_history(self, horse_id: str, limit: int = 10) -> pd.DataFrame:
        """
        馬の過去成績を取得

        Args:
            horse_id: 馬ID
            limit: 取得件数

        Returns:
            過去成績のDataFrame
        """
        query = """
        SELECT rr.*, r.date, r.venue, r.distance, r.track_type, r.track_condition
        FROM race_results rr
        LEFT JOIN races r ON rr.race_id = r.race_id
        WHERE rr.horse_id = ?
        ORDER BY r.date DESC
        LIMIT ?
        """
        return self.query_to_dataframe(query, (horse_id, limit))

    def race_exists(self, race_id: str) -> bool:
        """
        レースが既にデータベースに存在するかチェック

        Args:
            race_id: レースID

        Returns:
            存在する場合True
        """
        query = "SELECT COUNT(*) FROM races WHERE race_id = ?"
        result = self.execute_query(query, (race_id,))
        return result[0][0] > 0 if result else False

    def get_statistics(self) -> Dict[str, int]:
        """
        データベース統計情報を取得

        Returns:
            統計情報の辞書
        """
        stats = {}
        conn = self.connect()
        cursor = conn.cursor()

        tables = ['races', 'horses', 'race_results', 'jockeys', 'trainers',
                  'odds', 'training', 'predictions']

        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            stats[table] = count

        return stats

    def __enter__(self):
        """コンテキストマネージャーのエントリ"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャーの終了"""
        self.disconnect()
