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
        self.fetch_pedigree = self.config.get('scraping.fetch_pedigree', False)

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
            'races_skipped': 0,
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

                # netkeibaはEUC-JPエンコーディングを使用
                response.encoding = 'euc-jp'

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
        フォーマット: 年(4) + 競馬場(2) + 回次(2) + 日次(2) + レース番号(2)

        Args:
            date: 開催日
            venue_code: 競馬場コード
            race_number: レース番号
            day_count: 日数カウント（その開催の何日目か）
            times: 回次（年何回目の開催か）

        Returns:
            レースID (例: 2023年東京1回2日目12R = 202305010212)
        """
        year = date.strftime('%Y')
        venue_str = venue_code.zfill(2)
        times_str = str(times).zfill(2)
        day_str = str(day_count).zfill(2)
        race_str = str(race_number).zfill(2)

        # 正しい順番: 年 + 競馬場 + 回次 + 日次 + レース番号
        return f"{year}{venue_str}{times_str}{day_str}{race_str}"

    def scrape_horse_pedigree(self, horse_id: str) -> Optional[Dict[str, Any]]:
        """
        馬の血統情報をスクレイピング

        Args:
            horse_id: 馬ID

        Returns:
            血統情報の辞書
        """
        url = urljoin(self.base_url, f"horse/{horse_id}/")
        html = self.fetch_url(url)

        if not html:
            return None

        # 血統情報をパース
        pedigree = self.parser.parse_horse_pedigree(html, horse_id)

        if pedigree:
            self.logger.debug(f"Fetched pedigree for horse {horse_id}")
            return pedigree

        return None

    def scrape_race(self, race_id: str, fetch_pedigree: bool = False, skip_db_check: bool = False) -> bool:
        """
        特定のレースをスクレイピング

        Args:
            race_id: レースID
            fetch_pedigree: 血統情報も取得するか（追加リクエストが必要）
            skip_db_check: DBチェックをスキップするか（既にチェック済みの場合）

        Returns:
            成功したかどうか
        """
        # DBチェックをスキップしない場合のみチェック
        if not skip_db_check and self.db_manager.race_exists(race_id):
            self.logger.info(f"⏭ Race {race_id} already exists, skipping (no request)")
            self.stats['races_skipped'] += 1
            return True  # スキップは成功とみなす

        url = urljoin(self.base_url, f"race/{race_id}/")
        html = self.fetch_url(url)

        if not html:
            # 404エラー等でレースが存在しない場合
            self.logger.debug(f"Race {race_id} not found (404 or error)")
            return False

        # レース情報をパース
        race_info = self.parser.parse_race_info(html, race_id)
        if not race_info:
            # 存在しないレースまたはパースエラー（正常なケース）
            self.logger.warning(f"Race {race_id} not found or parse failed (no race data) - checking HTML")
            return False

        # レース結果をパース
        race_results = self.parser.parse_race_results(html, race_id)
        if not race_results:
            # 結果が未確定または存在しない（正常なケース）
            self.logger.warning(f"No race results found for {race_id} (未確定or存在しない)")
            return False

        # 払戻金情報をパース
        payouts = self.parser.parse_payouts(html, race_id)

        # データベースに保存
        try:
            # レース情報を保存
            if self.db_manager.insert_race(race_info):
                self.stats['races_saved'] += 1
                self.logger.info(f"Saved race: {race_info['race_name']} ({race_id})")

            # レース結果を保存
            for result in race_results:
                # 血統情報を取得（オプション）
                sire = None
                dam = None
                damsire = None

                if fetch_pedigree and result.get('horse_id'):
                    pedigree = self.scrape_horse_pedigree(result['horse_id'])
                    if pedigree:
                        sire = pedigree.get('sire')
                        dam = pedigree.get('dam')
                        damsire = pedigree.get('damsire')

                # 馬情報を保存
                horse_data = {
                    'horse_id': result['horse_id'],
                    'horse_name': result['horse_name'],
                    'sex': result.get('sex'),
                    'birth_date': None,  # 詳細ページから取得が必要
                    'sire': sire,
                    'dam': dam,
                    'damsire': damsire,
                    'breeder': None,
                    'owner': None
                }
                self.db_manager.insert_horse(horse_data)

                # レース結果を保存
                if self.db_manager.insert_race_result(result):
                    self.stats['results_saved'] += 1

            # 払戻金情報を保存
            for payout in payouts:
                self.db_manager.execute_update(
                    """
                    INSERT INTO payouts (race_id, payout_type, combination, payout, popularity)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (payout['race_id'], payout['payout_type'], payout['combination'],
                     payout['payout'], payout.get('popularity'))
                )

            self.logger.info(f"Saved {len(race_results)} results and {len(payouts)} payouts for race {race_id}")
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

        # スクレイピング実行（最適化版）
        self._scrape_smart(start_date, end_date, venues, progress_callback)

        # 最終統計
        self._log_stats()
        self.logger.info("Scraping completed")

        return self.stats

    def _scrape_smart(self, start_date: datetime, end_date: datetime,
                     venues: List[str], progress_callback=None):
        """
        日付ベースでレースリストを取得してスクレイピング

        Args:
            start_date: 開始日
            end_date: 終了日
            venues: 競馬場リスト（使用しない：日付からすべての競馬場を取得）
            progress_callback: 進捗コールバック
        """
        # 日付範囲の総日数を計算
        total_days = (end_date - start_date).days + 1
        current_date = start_date
        processed = 0

        self.logger.info(f"Scanning {total_days} days for races")

        # 日付ごとにループ
        while current_date <= end_date:
            processed += 1
            date_str = current_date.strftime('%Y%m%d')

            if progress_callback:
                msg = f"Checking {current_date.strftime('%Y-%m-%d')} (Saved: {self.stats['races_saved']}, Skipped: {self.stats['races_skipped']})"
                progress_callback(processed, total_days, msg)

            # その日のレースリストを取得
            race_ids = self._fetch_race_list_for_date(date_str)

            if race_ids:
                self.logger.info(f"Found {len(race_ids)} races on {current_date.strftime('%Y-%m-%d')}")

                # 各レースをスクレイピング
                for idx, race_id in enumerate(race_ids, 1):
                    if progress_callback:
                        msg = f"Processing {race_id} [{current_date.strftime('%Y-%m-%d')}] ({idx}/{len(race_ids)}) (Saved: {self.stats['races_saved']}, Skipped: {self.stats['races_skipped']})"
                        progress_callback(processed, total_days, msg)

                    self._race_exists_or_fetch(race_id)

                # 統計を定期的に出力
                if processed % 30 == 0:
                    self._log_stats()
            else:
                self.logger.debug(f"No races found on {current_date.strftime('%Y-%m-%d')}")

            # 次の日へ
            current_date += timedelta(days=1)

    def _fetch_race_list_for_date(self, date_str: str) -> List[str]:
        """
        特定日付のレースリストを取得

        Args:
            date_str: 日付文字列（YYYYMMDD形式）

        Returns:
            レースIDのリスト
        """
        url = urljoin(self.base_url, f"race/list/{date_str}/")
        html = self.fetch_url(url)

        if not html:
            return []

        # レースリストをパース
        race_ids = self.parser.parse_race_list(html)
        return race_ids

    def _race_exists_or_fetch(self, race_id: str) -> bool:
        """
        レースがDBに存在するか、またはフェッチできるかをチェック

        Args:
            race_id: レースID

        Returns:
            レースが存在する、またはフェッチに成功した場合True
        """
        # DBに存在する場合はスキップ（HTTPリクエスト不要）
        if self.db_manager.race_exists(race_id):
            self.logger.info(f"⏭ Race {race_id} already exists, skipping (no request)")
            self.stats['races_skipped'] += 1
            return True

        # フェッチを試みる（既にDBチェック済みなのでスキップ）
        return self.scrape_race(race_id, fetch_pedigree=self.fetch_pedigree, skip_db_check=True)

    def _get_race_date(self, race_id: str) -> Optional[str]:
        """
        レースIDからデータベースの開催日を取得

        Args:
            race_id: レースID

        Returns:
            開催日（YYYY-MM-DD形式）、存在しない場合はNone
        """
        try:
            query = "SELECT date FROM races WHERE race_id = ?"
            result = self.db_manager.execute_query(query, (race_id,))
            if result and len(result) > 0:
                return result[0][0]  # date列を返す
        except Exception as e:
            self.logger.debug(f"Failed to get race date for {race_id}: {e}")
        return None

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
        self.logger.info(f"✅ Races saved: {self.stats['races_saved']}")
        self.logger.info(f"⏭ Races skipped (already in DB): {self.stats['races_skipped']}")
        self.logger.info(f"Results saved: {self.stats['results_saved']}")

        if self.stats['total_requests'] > 0:
            success_rate = (self.stats['successful_requests'] / self.stats['total_requests']) * 100
            self.logger.info(f"Success rate: {success_rate:.2f}%")

        # スキップ効率を表示
        total_processed = self.stats['races_saved'] + self.stats['races_skipped']
        if total_processed > 0:
            skip_rate = (self.stats['races_skipped'] / total_processed) * 100
            self.logger.info(f"Skip efficiency: {skip_rate:.1f}% (saved {self.stats['races_skipped']} HTTP requests)")

    def close(self):
        """セッションをクローズ"""
        self.session.close()
        self.logger.info("Scraper session closed")
