"""
netkeiba.comスクレイパーモジュール
レースデータを取得してデータベースに保存
"""

import requests
import time
import random
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from urllib.parse import urljoin

from src.scraper.parser import NetkeibaParser
from src.database.db_manager import DatabaseManager
from src.utils.logger import Logger
from src.utils.config import Config


class NetkeibaScraper:
    """netkeiba.comスクレイパー"""

    # 競馬場コード
    VENUE_CODES = {
        '札幌': '01',
        '函館': '02',
        '福島': '03',
        '新潟': '04',
        '東京': '05',
        '中山': '06',
        '中京': '07',
        '京都': '08',
        '阪神': '09',
        '小倉': '10'
    }

    def __init__(self, db_manager: DatabaseManager, config: Optional[Config] = None):
        """
        Args:
            db_manager: データベースマネージャー
            config: 設定オブジェクト
        """
        self.db_manager = db_manager
        self.config = config or Config()
        self.logger = Logger.get_logger('scraper')
        self.parser = NetkeibaParser()

        # 設定値の取得
        self.base_url = self.config.get('scraping.base_url', 'https://db.netkeiba.com/')
        self.sleep_min = self.config.get('scraping.sleep_min', 2.0)
        self.sleep_max = self.config.get('scraping.sleep_max', 5.0)
        self.user_agent = self.config.get('scraping.user_agent', 'Mozilla/5.0')
        self.timeout = self.config.get('scraping.timeout', 30)

        # セッション設定
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })

        # 統計
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'races_saved': 0,
            'results_saved': 0
        }

    def fetch_url(self, url: str, retries: int = 3) -> Optional[str]:
        """
        URLからHTMLを取得

        Args:
            url: 取得するURL
            retries: リトライ回数

        Returns:
            HTML文字列
        """
        for attempt in range(retries):
            try:
                self.logger.info(f"Fetching: {url}")
                self.stats['total_requests'] += 1

                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()

                self.stats['successful_requests'] += 1

                # スリープ（サーバー負荷軽減）
                sleep_time = random.uniform(self.sleep_min, self.sleep_max)
                self.logger.debug(f"Sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)

                return response.text

            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Request failed (attempt {attempt + 1}/{retries}): {e}")
                self.stats['failed_requests'] += 1

                if attempt < retries - 1:
                    time.sleep(5 * (attempt + 1))  # 指数バックオフ
                else:
                    self.logger.error(f"Failed to fetch {url} after {retries} attempts")

        return None

    def generate_race_id(self, date: datetime, venue_code: str, race_number: int,
                        day_count: int = 1, times: int = 1) -> str:
        """
        レースIDを生成

        Args:
            date: 開催日
            venue_code: 競馬場コード
            race_number: レース番号
            day_count: 日数カウント（その開催の何日目か）
            times: 回次（年何回目の開催か）

        Returns:
            レースID (例: 202301050112)
        """
        year = date.strftime('%Y')
        times_str = str(times).zfill(2)
        day_str = str(day_count).zfill(2)
        venue_str = venue_code.zfill(2)
        race_str = str(race_number).zfill(2)

        return f"{year}{times_str}{day_str}{venue_str}{race_str}"

    def scrape_race(self, race_id: str) -> bool:
        """
        特定のレースをスクレイピング

        Args:
            race_id: レースID

        Returns:
            成功したかどうか
        """
        url = urljoin(self.base_url, f"race/{race_id}/")
        html = self.fetch_url(url)

        if not html:
            return False

        # レース情報をパース
        race_info = self.parser.parse_race_info(html, race_id)
        if not race_info:
            self.logger.warning(f"Failed to parse race info: {race_id}")
            return False

        # レース結果をパース
        race_results = self.parser.parse_race_results(html, race_id)
        if not race_results:
            self.logger.warning(f"No race results found: {race_id}")
            return False

        # データベースに保存
        try:
            # レース情報を保存
            if self.db_manager.insert_race(race_info):
                self.stats['races_saved'] += 1
                self.logger.info(f"Saved race: {race_info['race_name']} ({race_id})")

            # レース結果を保存
            for result in race_results:
                # 馬情報を保存
                horse_data = {
                    'horse_id': result['horse_id'],
                    'horse_name': result['horse_name'],
                    'sex': result.get('sex'),
                    'birth_date': None,  # 詳細ページから取得が必要
                    'sire': None,
                    'dam': None,
                    'damsire': None,
                    'breeder': None,
                    'owner': None
                }
                self.db_manager.insert_horse(horse_data)

                # レース結果を保存
                if self.db_manager.insert_race_result(result):
                    self.stats['results_saved'] += 1

            self.logger.info(f"Saved {len(race_results)} results for race {race_id}")
            return True

        except Exception as e:
            self.logger.error(f"Database error for race {race_id}: {e}")
            return False

    def scrape_date_range(self, start_date: datetime, end_date: datetime,
                         venues: Optional[List[str]] = None,
                         progress_callback=None) -> Dict[str, int]:
        """
        日付範囲でレースをスクレイピング

        Args:
            start_date: 開始日
            end_date: 終了日
            venues: 対象競馬場リスト（Noneの場合は全競馬場）
            progress_callback: 進捗コールバック関数 (current, total, message)

        Returns:
            統計情報の辞書
        """
        self.logger.info(f"Starting scrape from {start_date} to {end_date}")

        if venues is None:
            venues = list(self.VENUE_CODES.keys())

        # レースID候補を生成
        race_ids = self._generate_race_id_candidates(start_date, end_date, venues)
        total_candidates = len(race_ids)

        self.logger.info(f"Generated {total_candidates} race ID candidates")

        # スクレイピング実行
        for idx, race_id in enumerate(race_ids, 1):
            if progress_callback:
                progress_callback(idx, total_candidates, f"Scraping race {race_id}")

            self.scrape_race(race_id)

            # 定期的に統計をログ出力
            if idx % 50 == 0:
                self._log_stats()

        # 最終統計
        self._log_stats()
        self.logger.info("Scraping completed")

        return self.stats

    def _generate_race_id_candidates(self, start_date: datetime, end_date: datetime,
                                    venues: List[str]) -> List[str]:
        """
        日付範囲と競馬場からレースID候補を生成

        Args:
            start_date: 開始日
            end_date: 終了日
            venues: 競馬場リスト

        Returns:
            レースIDのリスト
        """
        race_ids = []

        # 年ごとに処理
        current_date = start_date
        while current_date <= end_date:
            year = current_date.year

            # 各競馬場について
            for venue in venues:
                venue_code = self.VENUE_CODES.get(venue)
                if not venue_code:
                    continue

                # 各開催回（年間最大6回程度）
                for times in range(1, 7):
                    # 各開催日（1回の開催で最大8日程度）
                    for day_count in range(1, 9):
                        # 各レース（1日最大12レース）
                        for race_num in range(1, 13):
                            race_id = self.generate_race_id(
                                current_date, venue_code, race_num, day_count, times
                            )
                            race_ids.append(race_id)

            current_date = datetime(current_date.year + 1, 1, 1)
            if current_date.year > end_date.year:
                break

        return race_ids

    def _log_stats(self):
        """統計情報をログ出力"""
        self.logger.info("=== Scraping Statistics ===")
        self.logger.info(f"Total requests: {self.stats['total_requests']}")
        self.logger.info(f"Successful: {self.stats['successful_requests']}")
        self.logger.info(f"Failed: {self.stats['failed_requests']}")
        self.logger.info(f"Races saved: {self.stats['races_saved']}")
        self.logger.info(f"Results saved: {self.stats['results_saved']}")

        if self.stats['total_requests'] > 0:
            success_rate = (self.stats['successful_requests'] / self.stats['total_requests']) * 100
            self.logger.info(f"Success rate: {success_rate:.2f}%")

    def close(self):
        """セッションをクローズ"""
        self.session.close()
        self.logger.info("Scraper session closed")
