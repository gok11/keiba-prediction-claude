"""
プレミアムログインの実際のテスト
実際にnetkeiba.comにログインして、プレミアム情報が取得できるか確認
"""

import sys
import os
from dotenv import load_dotenv

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.scraper.netkeiba_scraper import NetkeibaScraper
from src.database.db_manager import DatabaseManager
from src.utils.config import Config


def test_premium_login():
    """実際にログインしてプレミアム情報が取得できるか確認"""
    print("=== プレミアムログインの実テスト ===\n")

    # .envファイルから認証情報を読み込み
    load_dotenv()
    username = os.getenv('NETKEIBA_USERNAME')
    password = os.getenv('NETKEIBA_PASSWORD')

    if not username or not password:
        print("❌ エラー: .envファイルにNETKEIBA_USERNAMEとNETKEIBA_PASSWORDが設定されていません")
        return False

    print(f"認証情報を確認:")
    print(f"  ユーザー名: {username[:3]}***")
    print(f"  パスワード: ***\n")

    # データベースとスクレイパーを初期化
    db = DatabaseManager("data/keiba.db")
    db.connect()
    config = Config()
    scraper = NetkeibaScraper(db, config)

    # ログイン状態を確認
    print("ログイン試行中...")
    if scraper.is_logged_in:
        print("✅ ログイン成功\n")
    else:
        print("❌ ログイン失敗\n")
        return False

    # 実際にテストレースページにアクセス
    test_race_id = "202408030211"
    print(f"テストレースページにアクセス: {test_race_id}")
    race_url = f"https://db.netkeiba.com/race/{test_race_id}/"
    html = scraper.fetch_url(race_url)

    if not html:
        print("❌ レースページの取得に失敗")
        return False

    # プレミアム情報が含まれているか確認
    print("\nプレミアム情報の確認:")

    checks = [
        ("馬場指数", "馬場指数" in html),
        ("タイム指数", "タイム指数" in html),
        ("馬場コメント", "馬場コメント" in html),
        ("レース分析", "分析コメント" in html or "レース分析" in html),
        ("注目馬短評", "注目馬" in html and "短評" in html),
    ]

    all_passed = True
    for name, result in checks:
        status = "✅" if result else "❌"
        print(f"  {status} {name}: {'あり' if result else 'なし'}")
        if not result:
            all_passed = False

    # エラーメッセージがないか確認
    print("\nエラーメッセージの確認:")
    error_checks = [
        ("プレミアムサービス", "プレミアムサービス" in html),
        ("プレミアム会員限定", "プレミアム会員限定" in html),
    ]

    for name, result in error_checks:
        status = "❌" if result else "✅"
        print(f"  {status} {name}: {'検出' if result else '検出なし'}")
        if result:
            all_passed = False

    # パーサーでプレミアム情報を取得してみる
    print("\nプレミアム情報のパース:")
    premium_info = scraper.parser.parse_premium_race_info(html, test_race_id)

    if premium_info:
        print(f"  ✅ 馬場指数: {premium_info.get('track_index', 'なし')}")
        print(f"  ✅ 馬場コメント: {len(premium_info.get('track_comment', ''))} 文字")
        print(f"  ✅ レース分析: {len(premium_info.get('race_analysis_comment', ''))} 文字")
        print(f"  ✅ 注目馬短評: {len(premium_info.get('horse_short_reviews', []))} 件")

        # 短評の例を表示
        reviews = premium_info.get('horse_short_reviews', [])
        if reviews:
            print("\n  短評の例:")
            for review in reviews[:2]:  # 最初の2件
                print(f"    {review.get('finishing_position')}着 {review.get('horse_name')}")
    else:
        print("  ❌ プレミアム情報のパースに失敗")
        all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("✅ すべてのテストに合格しました")
        return True
    else:
        print("❌ 一部のテストに失敗しました")
        return False


if __name__ == "__main__":
    success = test_premium_login()
    sys.exit(0 if success else 1)
