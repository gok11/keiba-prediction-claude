"""
設定管理モジュール
config/settings.json を読み込み・管理
"""

import json
from pathlib import Path
from typing import Any, Dict


class Config:
    """設定管理クラス"""

    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._config is None:
            self.load_config()

    def load_config(self, config_path: str = "config/settings.json"):
        """設定ファイルを読み込む"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
        except FileNotFoundError:
            # デフォルト設定
            self._config = {
                "app": {"name": "競馬予想システム", "version": "1.0.0"},
                "database": {"path": "data/keiba.db"},
                "scraping": {
                    "base_url": "https://db.netkeiba.com/",
                    "sleep_min": 2.0,
                    "sleep_max": 5.0,
                    "parallel_count": 1,
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "timeout": 30
                },
                "ml": {
                    "default_model": "LightGBM",
                    "test_size": 0.2,
                    "random_state": 42,
                    "cv_folds": 5
                }
            }

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        設定値を取得

        Args:
            key_path: ドット区切りのキーパス（例: "scraping.base_url"）
            default: デフォルト値

        Returns:
            設定値
        """
        keys = key_path.split('.')
        value = self._config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, key_path: str, value: Any):
        """
        設定値を設定

        Args:
            key_path: ドット区切りのキーパス
            value: 設定値
        """
        keys = key_path.split('.')
        config = self._config

        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        config[keys[-1]] = value

    def save(self, config_path: str = "config/settings.json"):
        """設定ファイルを保存"""
        Path(config_path).parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, ensure_ascii=False, indent=2)
