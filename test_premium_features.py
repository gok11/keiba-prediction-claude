"""
プレミアム機能のテストスクリプト
testrace.htmlを使用してプレミアム情報のパースと保存をテスト
"""

import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.scraper.parser import NetkeibaParser
from src.database.db_manager import DatabaseManager


def test_premium_parsing():
    """testrace.htmlからプレミアム情報をパース"""
    print("=== テスト: testrace.html からプレミアム情報をパース ===")

    # HTMLファイルを読み込み
    with open('testrace.html', 'r', encoding='utf-8') as f:
        html = f.read()

    parser = NetkeibaParser()
    race_id = "202408030211"  # テストレースID

    # 基本情報をパース
    print("\n1. レース基本情報をパース...")
    race_info = parser.parse_race_info(html, race_id)
    if race_info:
        print(f"   ✓ レース名: {race_info.get('race_name')}")
        print(f"   ✓ 日付: {race_info.get('date')}")
        print(f"   ✓ 競馬場: {race_info.get('venue')}")
    else:
        print("   ✗ レース情報のパースに失敗")
        return False

    # プレミアム情報をパース
    print("\n2. プレミアム情報をパース...")
    premium_info = parser.parse_premium_race_info(html, race_id)
    if premium_info:
        print(f"   ✓ 馬場指数: {premium_info.get('track_index')}")
        print(f"   ✓ 馬場コメント: {premium_info.get('track_comment', 'なし')[:50]}...")
        print(f"   ✓ レース分析: {premium_info.get('race_analysis_comment', 'なし')[:50]}...")
        print(f"   ✓ 注目馬短評: {len(premium_info.get('horse_short_reviews', []))} 件")

        # 短評の詳細を表示
        reviews = premium_info.get('horse_short_reviews', [])
        if reviews:
            print("\n   注目馬短評の例:")
            for review in reviews[:3]:  # 最初の3件のみ表示
                print(f"   - {review.get('horse_name')}: {review.get('review', '')[:60]}...")
    else:
        print("   ✗ プレミアム情報のパースに失敗")
        return False

    # レース結果をパース
    print("\n3. レース結果（プレミアム情報含む）をパース...")
    results = parser.parse_race_results(html, race_id)
    if results:
        print(f"   ✓ 結果件数: {len(results)} 件")

        # プレミアム情報が含まれているか確認
        premium_count = sum(1 for r in results if r.get('time_index') or r.get('remarks'))
        print(f"   ✓ プレミアム情報あり: {premium_count} 件")

        # 最初の結果の詳細を表示
        if results:
            first = results[0]
            print(f"\n   1着の詳細:")
            print(f"   - 馬名: {first.get('horse_name')}")
            print(f"   - タイム指数: {first.get('time_index')}")
            print(f"   - 備考: {first.get('remarks', 'なし')}")
    else:
        print("   ✗ レース結果のパースに失敗")
        return False

    print("\n=== パーステスト完了 ===\n")
    return True


def test_database_save():
    """データベースへの保存をテスト"""
    print("=== テスト: データベースへの保存 ===")

    # テスト用データベースを作成
    test_db = "data/test_premium.db"
    if os.path.exists(test_db):
        os.remove(test_db)

    db = DatabaseManager(test_db)
    db.connect()
    db.initialize_database()
    print("✓ テスト用データベースを作成")

    # HTMLファイルを読み込み
    with open('testrace.html', 'r', encoding='utf-8') as f:
        html = f.read()

    parser = NetkeibaParser()
    race_id = "202408030211"

    # データをパース
    race_info = parser.parse_race_info(html, race_id)
    premium_info = parser.parse_premium_race_info(html, race_id)
    results = parser.parse_race_results(html, race_id)

    # プレミアム情報をrace_infoに統合
    if premium_info:
        race_info['track_index'] = premium_info.get('track_index')
        race_info['track_comment'] = premium_info.get('track_comment')
        race_info['race_analysis_comment'] = premium_info.get('race_analysis_comment')

    # レース情報を保存
    print("\n1. レース情報を保存...")
    if db.insert_race(race_info):
        print("   ✓ レース情報を保存")
    else:
        print("   ✗ レース情報の保存に失敗")
        return False

    # レース結果を保存
    print("\n2. レース結果を保存...")
    for result in results:
        # 馬情報を保存
        horse_data = {
            'horse_id': result['horse_id'],
            'horse_name': result['horse_name'],
            'sex': result.get('sex'),
            'birth_date': None,
            'sire': None,
            'dam': None,
            'damsire': None,
            'breeder': None,
            'owner': None
        }
        db.insert_horse(horse_data)

        # レース結果を保存
        db.insert_race_result(result)
    print(f"   ✓ {len(results)} 件のレース結果を保存")

    # 注目馬短評を保存
    print("\n3. 注目馬短評を保存...")
    if premium_info:
        reviews = premium_info.get('horse_short_reviews', [])
        # horse_nameからhorse_idをマッピング
        horse_name_to_id = {result['horse_name']: result['horse_id'] for result in results}
        saved_count = 0
        for review in reviews:
            horse_name = review.get('horse_name')
            if horse_name in horse_name_to_id:
                review['horse_id'] = horse_name_to_id[horse_name]
                db.insert_horse_short_review(review)
                saved_count += 1
            else:
                print(f"   ⚠ Horse not found in results: {horse_name}")
        print(f"   ✓ {saved_count} 件の短評を保存")

    # データベースから読み込んで確認
    print("\n4. データベースから読み込んで確認...")
    query = """
    SELECT race_name, track_index, track_comment, race_analysis_comment
    FROM races WHERE race_id = ?
    """
    result = db.execute_query(query, (race_id,))
    if result and len(result) > 0:
        row = result[0]
        print(f"   ✓ レース名: {row[0]}")
        print(f"   ✓ 馬場指数: {row[1]}")
        print(f"   ✓ 馬場コメント: {row[2][:50] if row[2] else 'なし'}...")
        print(f"   ✓ レース分析: {row[3][:50] if row[3] else 'なし'}...")

    query = """
    SELECT COUNT(*) FROM race_results WHERE race_id = ? AND time_index IS NOT NULL
    """
    result = db.execute_query(query, (race_id,))
    if result:
        count = result[0][0]
        print(f"   ✓ タイム指数あり: {count} 件")

    query = """
    SELECT COUNT(*) FROM horse_short_reviews WHERE race_id = ?
    """
    result = db.execute_query(query, (race_id,))
    if result:
        count = result[0][0]
        print(f"   ✓ 注目馬短評: {count} 件")

    db.disconnect()
    print("\n=== データベーステスト完了 ===\n")
    print(f"テスト用データベース: {test_db}")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("プレミアム機能テスト")
    print("=" * 60 + "\n")

    # パーステスト
    if not test_premium_parsing():
        print("\n❌ パーステストに失敗しました")
        sys.exit(1)

    # データベーステスト
    if not test_database_save():
        print("\n❌ データベーステストに失敗しました")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✅ すべてのテストに成功しました！")
    print("=" * 60)
