"""
スクレイピングワーカースレッド
バックグラウンドでスクレイピングを実行
"""

from PyQt6.QtCore import QThread, pyqtSignal
from datetime import datetime
from typing import Dict, Any

from src.scraper.netkeiba_scraper import NetkeibaScraper
from src.database.db_manager import DatabaseManager
from src.utils.config import Config


class ScrapingWorker(QThread):
    """スクレイピングワーカースレッド"""

    # シグナル定義
    progress_updated = pyqtSignal(int, int, str)  # (current, total, message)
    log_message = pyqtSignal(str)  # ログメッセージ
    scraping_finished = pyqtSignal(dict)  # 統計情報
    scraping_error = pyqtSignal(str)  # エラーメッセージ

    def __init__(self, db_manager: DatabaseManager, config: Dict[str, Any]):
        """
        Args:
            db_manager: データベースマネージャー
            config: スクレイピング設定
        """
        super().__init__()
        self.db_manager = db_manager
        self.config_dict = config
        self.scraper = None
        self._is_running = True

    def run(self):
        """スレッド実行"""
        try:
            self.log_message.emit("スクレイピングを開始します...")

            # 設定を Config オブジェクトに適用
            app_config = Config()
            app_config.set('scraping.sleep_min', self.config_dict['sleep_min'])
            app_config.set('scraping.sleep_max', self.config_dict['sleep_max'])
            app_config.set('scraping.fetch_pedigree', self.config_dict.get('fetch_pedigree', True))

            # スクレイパーの初期化
            self.scraper = NetkeibaScraper(self.db_manager, app_config)

            # 日付の解析
            start_date = datetime.strptime(self.config_dict['start_date'], '%Y-%m-%d')
            end_date = datetime.strptime(self.config_dict['end_date'], '%Y-%m-%d')

            self.log_message.emit(f"期間: {start_date.date()} ～ {end_date.date()}")
            self.log_message.emit(f"スリープ時間: {self.config_dict['sleep_min']}～{self.config_dict['sleep_max']}秒")
            self.log_message.emit(f"血統情報取得: {'有効' if self.config_dict.get('fetch_pedigree', True) else '無効'}")

            # 進捗コールバック
            def progress_callback(current, total, message):
                if not self._is_running:
                    raise InterruptedError("スクレイピングが中止されました")
                self.progress_updated.emit(current, total, message)
                self.log_message.emit(f"[{current}/{total}] {message}")

            # スクレイピング実行
            stats = self.scraper.scrape_date_range(
                start_date,
                end_date,
                progress_callback=progress_callback
            )

            # 完了
            self.log_message.emit("=" * 50)
            self.log_message.emit("スクレイピングが完了しました！")
            self.log_message.emit(f"総リクエスト数: {stats['total_requests']}")
            self.log_message.emit(f"成功: {stats['successful_requests']}")
            self.log_message.emit(f"失敗: {stats['failed_requests']}")
            self.log_message.emit(f"保存されたレース数: {stats['races_saved']}")
            self.log_message.emit(f"スキップされたレース数: {stats['races_skipped']}")
            self.log_message.emit(f"保存された結果数: {stats['results_saved']}")

            self.scraping_finished.emit(stats)

        except InterruptedError as e:
            self.log_message.emit(str(e))
            self.scraping_error.emit(str(e))

        except Exception as e:
            error_msg = f"スクレイピングエラー: {str(e)}"
            self.log_message.emit(error_msg)
            self.scraping_error.emit(error_msg)

        finally:
            if self.scraper:
                self.scraper.close()

    def stop(self):
        """スクレイピングを中止"""
        self._is_running = False
        self.log_message.emit("中止要求を受け付けました...")
