"""
ロガー設定モジュール
アプリケーション全体で使用するロガーを提供
"""

import logging
import os
from pathlib import Path
from datetime import datetime


class Logger:
    """ロガー管理クラス"""

    _loggers = {}

    @staticmethod
    def get_logger(name: str, log_to_file: bool = True) -> logging.Logger:
        """
        ロガーを取得（シングルトン）

        Args:
            name: ロガー名
            log_to_file: ファイルに出力するか

        Returns:
            ロガーインスタンス
        """
        if name in Logger._loggers:
            return Logger._loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        # フォーマッター
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)-8s %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # コンソールハンドラー
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # ファイルハンドラー
        if log_to_file:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)

            today = datetime.now().strftime("%Y%m%d")
            log_file = log_dir / f"{name}_{today}.log"

            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        Logger._loggers[name] = logger
        return logger
