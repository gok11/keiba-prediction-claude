"""
netkeiba.comスクレイパーモジュール
レースデータを取得してデータベースに保存
"""

import requests
import time
import random
import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from urllib.parse import urljoin
from dotenv import load_dotenv

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
        self.fetch_premium_training = self.config.get('scraping.fetch_premium_training', True)

        # セッション設定
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })

        # ログイン情報を読み込み
        load_dotenv()
        self.username = os.getenv('NETKEIBA_USERNAME')
        self.password = os.getenv('NETKEIBA_PASSWORD')
        self.is_logged_in = False

        # プレミアム会員の場合は自動ログイン
        if self.username and self.password:
            self.login()

        # 統計
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'races_saved': 0,
            'races_skipped': 0,
            'results_saved': 0
        }

        # 失敗したレースを記録
        self.failed_races = []

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

    def login(self) -> bool:
        """
        netkeiba.comにログイン

        Returns:
            ログイン成功: True, 失敗: False
        """
        if not self.username or not self.password:
            self.logger.warning("ログイン情報が設定されていません")
            return False

        try:
            self.logger.info("netkeiba.comにログイン中...")

            # ログインURL
            login_url = "https://regist.netkeiba.com/account/?pid=login"

            # ログインページにアクセス（セッション確立）
            login_page = self.session.get(login_url, timeout=self.timeout)
            login_page.encoding = 'euc-jp'

            # ログイン情報をPOST
            # デバッグで判明した必要なhiddenフィールドを含める
            login_data = {
                'pid': 'login',
                'action': 'auth',
                'return_url2': '',
                'mem_tp': '',
                'login_id': self.username,
                'pswd': self.password,
            }

            response = self.session.post(
                login_url,
                data=login_data,
                timeout=self.timeout,
                allow_redirects=True
            )
            response.encoding = 'euc-jp'

            # ログイン成功の確認（プレミアム会員ページにアクセスできるか）
            # より厳密な確認：実際にプレミアム情報が含まれるページにアクセス
            # テストレースページにアクセスして、プレミアム情報が取得できるか確認
            test_race_url = "https://db.netkeiba.com/race/202408030211/"  # 既知のレース
            test_response = self.session.get(test_race_url, timeout=self.timeout)
            test_response.encoding = 'euc-jp'

            # プレミアム情報の実データを探す（数値が含まれているか）
            import re
            # 馬場指数はマイナス値もあるので-?を追加
            track_index_pattern = r'馬場指数[^\d\-]*(-?\d+\.?\d*)'
            # タイム指数はHTMLで「ﾀｲﾑ指数」と半角カタカナで表示されているため、
            # speed_indexクラスを持つtdタグから数値を抽出
            time_index_pattern = r'<td[^>]*class="[^"]*speed_index[^"]*"[^>]*>\s*(\d+)\s*</td>'
            has_track_index = re.search(track_index_pattern, test_response.text) is not None
            has_time_index = re.search(time_index_pattern, test_response.text) is not None

            # プレミアム会員限定のエラーメッセージがあるか確認
            # より具体的なパターンで誤検出を防ぐ（フッターの「プレミアムサービスのご案内」などは除外）
            error_patterns = [
                'プレミアムサービスにご登録',
                'プレミアム会員限定の情報',
                'プレミアムコンテンツです',
                'プレミアム会員のみ',
                'プレミアムサービスへの登録が必要',
            ]
            has_premium_error = any(pattern in test_response.text for pattern in error_patterns)

            # 実データがあればログイン成功
            if has_track_index or has_time_index:
                self.is_logged_in = True
                self.logger.info("ログイン成功（プレミアム情報へのアクセスを確認）")
                return True
            # エラーメッセージがあればログイン失敗
            elif has_premium_error:
                self.is_logged_in = False
                self.logger.warning("ログインに失敗しました（プレミアム会員限定メッセージが表示されています）")
                return False
            else:
                # どちらでもない場合（判定不能）
                self.is_logged_in = False
                self.logger.warning("ログイン状態を確認できません（プレミアム情報もエラーメッセージも見つかりません）")
                return False

        except Exception as e:
            self.logger.error(f"ログインエラー: {e}")
            return False

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

        血統詳細ページ (/horse/ped/{horse_id}/) から取得
        ※馬詳細ページの血統情報は動的ロードのため使用不可

        Args:
            horse_id: 馬ID

        Returns:
            血統情報の辞書
        """
        # 血統詳細ページから取得（静的HTMLで5代血統表が含まれる）
        url = urljoin(self.base_url, f"horse/ped/{horse_id}/")
        html = self.fetch_url(url)

        if not html:
            return None

        # 血統情報をパース
        pedigree = self.parser.parse_horse_pedigree(html, horse_id)

        if pedigree:
            self.logger.debug(f"Fetched pedigree for horse {horse_id}")
            return pedigree

        return None

    def scrape_race(self, race_id: str, fetch_pedigree: bool = False, skip_db_check: bool = False,
                    fetch_premium_training: bool = False) -> bool:
        """
        特定のレースをスクレイピング

        Args:
            race_id: レースID
            fetch_pedigree: 血統情報も取得するか（追加リクエストが必要）
            skip_db_check: DBチェックをスキップするか（既にチェック済みの場合）
            fetch_premium_training: プレミアム調教情報も取得するか（追加リクエストが必要）

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

        # プレミアム情報をパース（ログイン済みの場合のみ）
        premium_info = None
        if self.is_logged_in:
            premium_info = self.parser.parse_premium_race_info(html, race_id)
            if premium_info:
                # プレミアム情報をrace_infoに統合
                race_info['track_index'] = premium_info.get('track_index')
                race_info['track_comment'] = premium_info.get('track_comment')
                race_info['race_analysis_comment'] = premium_info.get('race_analysis_comment')
                self.logger.debug(f"Parsed premium race info for {race_id}")

        # レース結果をパース
        race_results = self.parser.parse_race_results(html, race_id)
        if not race_results:
            # 結果が未確定または存在しない（正常なケース）
            self.logger.warning(f"No race results found for {race_id} (未確定or存在しない)")
            return False

        # 払戻金情報をパース
        payouts = self.parser.parse_payouts(html, race_id)

        # ラップタイムをパース
        lap_times = self.parser.parse_lap_times(html, race_id)

        # 注目馬短評をパース（プレミアム情報が取得できている場合）
        horse_short_reviews = []
        if self.is_logged_in and premium_info:
            horse_short_reviews = premium_info.get('horse_short_reviews', [])

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
                birth_date = None

                if fetch_pedigree and result.get('horse_id'):
                    pedigree = self.scrape_horse_pedigree(result['horse_id'])
                    if pedigree:
                        sire = pedigree.get('sire')
                        dam = pedigree.get('dam')
                        damsire = pedigree.get('damsire')
                        birth_date = pedigree.get('birth_date')

                # 馬情報を保存
                horse_data = {
                    'horse_id': result['horse_id'],
                    'horse_name': result['horse_name'],
                    'sex': result.get('sex'),
                    'birth_date': birth_date,
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

            # ラップタイムを保存
            for lap_time in lap_times:
                self.db_manager.insert_lap_time(lap_time)

            # 注目馬短評を保存（プレミアム情報）
            # horse_nameからhorse_idをマッピング
            horse_name_to_id = {result['horse_name']: result['horse_id'] for result in race_results}
            for review in horse_short_reviews:
                # 馬名からhorse_idを取得
                horse_name = review.get('horse_name')
                if horse_name in horse_name_to_id:
                    review['horse_id'] = horse_name_to_id[horse_name]
                    self.db_manager.insert_horse_short_review(review)
                else:
                    self.logger.warning(f"Horse not found in results: {horse_name}")

            # 調教タイムと厩舎コメントを取得（オプション、追加リクエストが必要）
            if fetch_premium_training and self.is_logged_in:
                for result in race_results:
                    horse_id = result.get('horse_id')
                    if not horse_id:
                        continue

                    # 調教タイムを取得
                    training_url = urljoin(self.base_url, f"horse/{horse_id}/training/{race_id}/")
                    training_html = self.fetch_url(training_url)
                    if training_html:
                        training_times = self.parser.parse_training_times(training_html, horse_id, race_id)
                        for training in training_times:
                            self.db_manager.insert_training_detail(training)
                        self.logger.debug(f"Saved {len(training_times)} training records for horse {horse_id}")

                    # 厩舎コメントを取得
                    comment_url = urljoin(self.base_url, f"horse/{horse_id}/comment/{race_id}/")
                    comment_html = self.fetch_url(comment_url)
                    if comment_html:
                        comment = self.parser.parse_stable_comment(comment_html, horse_id, race_id)
                        if comment:
                            self.db_manager.insert_stable_comment({
                                'horse_id': horse_id,
                                'race_id': race_id,
                                'comment': comment
                            })
                            self.logger.debug(f"Saved stable comment for horse {horse_id}")

            premium_msg = ""
            if self.is_logged_in:
                premium_msg = f", {len(horse_short_reviews)} reviews"
                if fetch_premium_training:
                    premium_msg += " (with training data)"

            lap_msg = f", {len(lap_times)} lap times" if lap_times else ""
            self.logger.info(f"Saved {len(race_results)} results, {len(payouts)} payouts{lap_msg}{premium_msg} for race {race_id}")
            return True

        except Exception as e:
            self.logger.error(f"Database error for race {race_id}: {e}")
            # 失敗したレースを記録
            self.failed_races.append({
                'race_id': race_id,
                'error': str(e),
                'race_name': race_info.get('race_name', 'Unknown') if race_info else 'Unknown'
            })
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

        # 失敗したレースを保存
        self._save_failed_races()

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
        return self.scrape_race(
            race_id,
            fetch_pedigree=self.fetch_pedigree,
            fetch_premium_training=self.fetch_premium_training,
            skip_db_check=True
        )

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

        # 失敗したレース情報を表示
        if self.failed_races:
            self.logger.warning(f"❌ Failed races: {len(self.failed_races)}")
            self.logger.warning("Failed race details:")
            for failed in self.failed_races[:10]:  # 最初の10件のみ表示
                self.logger.warning(f"  - {failed['race_id']}: {failed['race_name']} - Error: {failed['error'][:50]}")
            if len(self.failed_races) > 10:
                self.logger.warning(f"  ... and {len(self.failed_races) - 10} more (see data/failed_races.txt)")

    def _save_failed_races(self):
        """失敗したレースをファイルに保存"""
        if not self.failed_races:
            return

        import os
        from datetime import datetime as dt

        # data ディレクトリを作成
        os.makedirs('data', exist_ok=True)

        # タイムスタンプ付きファイル名
        timestamp = dt.now().strftime('%Y%m%d_%H%M%S')
        filename = f'data/failed_races_{timestamp}.txt'

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Failed Races - {dt.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total: {len(self.failed_races)}\n")
                f.write("=" * 80 + "\n\n")

                for failed in self.failed_races:
                    f.write(f"Race ID: {failed['race_id']}\n")
                    f.write(f"Race Name: {failed['race_name']}\n")
                    f.write(f"Error: {failed['error']}\n")
                    f.write("-" * 80 + "\n")

            self.logger.info(f"Failed races saved to: {filename}")

            # 失敗したレースIDのみのファイルも作成（再実行用）
            retry_filename = 'data/retry_race_ids.txt'
            with open(retry_filename, 'w', encoding='utf-8') as f:
                for failed in self.failed_races:
                    f.write(f"{failed['race_id']}\n")

            self.logger.info(f"Retry race IDs saved to: {retry_filename}")

        except Exception as e:
            self.logger.error(f"Failed to save failed races: {e}")

    def retry_failed_races(self, race_ids_file: str = 'data/retry_race_ids.txt',
                           fetch_pedigree: bool = False,
                           progress_callback=None) -> Dict[str, int]:
        """
        失敗したレースIDのリストから再スクレイピング

        Args:
            race_ids_file: レースIDリストファイル
            fetch_pedigree: 血統情報を取得するか
            progress_callback: 進捗コールバック

        Returns:
            統計情報の辞書
        """
        import os

        if not os.path.exists(race_ids_file):
            self.logger.error(f"Race IDs file not found: {race_ids_file}")
            return self.stats

        # ファイルからレースIDを読み込み
        race_ids = []
        with open(race_ids_file, 'r', encoding='utf-8') as f:
            for line in f:
                race_id = line.strip()
                if race_id and race_id.isdigit() and len(race_id) == 12:
                    race_ids.append(race_id)

        self.logger.info(f"Loaded {len(race_ids)} race IDs from {race_ids_file}")

        if not race_ids:
            self.logger.warning("No valid race IDs found in file")
            return self.stats

        # 統計と失敗リストをリセット
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'races_saved': 0,
            'races_skipped': 0,
            'results_saved': 0
        }
        self.failed_races = []

        # 各レースをスクレイピング
        total = len(race_ids)
        for idx, race_id in enumerate(race_ids, 1):
            if progress_callback:
                msg = f"Retrying {race_id} ({idx}/{total}) (Saved: {self.stats['races_saved']}, Failed: {len(self.failed_races)})"
                progress_callback(idx, total, msg)

            self.scrape_race(race_id, fetch_pedigree=fetch_pedigree, skip_db_check=False)

            # 定期的に統計を出力
            if idx % 10 == 0:
                self._log_stats()

        # 最終統計
        self._log_stats()
        self._save_failed_races()

        self.logger.info("Retry completed")

        return self.stats

    def close(self):
        """セッションをクローズ"""
        self.session.close()
        self.logger.info("Scraper session closed")
