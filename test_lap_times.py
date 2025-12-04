"""
ラップタイム機能のテストスクリプト
testrace.htmlを使用してラップタイムのパースと保存をテスト
"""

import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.scraper.parser import NetkeibaParser
from src.database.db_manager import DatabaseManager


def test_lap_times_parsing():
    """testrace.htmlからラップタイムをパース"""
    print("=== テスト: testrace.html からラップタイムをパース ===\n")

    # HTMLファイルを読み込み
    with open('testrace.html', 'r', encoding='utf-8') as f:
        html = f.read()

    parser = NetkeibaParser()
    race_id = "202001010101"  # テストレースID

    # ラップタイムをパース
    print("1. ラップタイムをパース...")
    lap_times = parser.parse_lap_times(html, race_id)

    if lap_times:
        print(f"   ✓ ラップタイム: {len(lap_times)} 区間")
        print("\n   詳細:")
        for lap in lap_times:
            print(f"   - 区間 {lap['section']}: {lap['lap_time']}秒")
        print()
    else:
        print("   ✗ ラップタイムのパースに失敗")
        return False

    print("=== パーステスト完了 ===\n")
    return True


def test_lap_times_database():
    """データベースへの保存をテスト"""
    print("=== テスト: データベースへの保存 ===\n")

    # テスト用データベースを作成
    test_db = "data/test_lap_times.db"
    if os.path.exists(test_db):
        os.remove(test_db)

    db = DatabaseManager(test_db)
    db.connect()
    db.initialize_database()
    print("✓ テスト用データベースを作成\n")

    # HTMLファイルを読み込み
    with open('testrace.html', 'r', encoding='utf-8') as f:
        html = f.read()

    parser = NetkeibaParser()
    race_id = "202001010101"

    # レース情報を先に保存（外部キー制約のため）
    print("1. レース情報を保存...")
    race_info = parser.parse_race_info(html, race_id)
    if race_info and db.insert_race(race_info):
        print(f"   ✓ レース名: {race_info['race_name']}\n")
    else:
        print("   ✗ レース情報の保存に失敗\n")
        return False

    # ラップタイムをパース
    lap_times = parser.parse_lap_times(html, race_id)

    # ラップタイムを保存
    print("2. ラップタイムを保存...")
    saved_count = 0
    for lap_time in lap_times:
        if db.insert_lap_time(lap_time):
            saved_count += 1
    print(f"   ✓ {saved_count} 区間のラップタイムを保存\n")

    # データベースから読み込んで確認
    print("3. データベースから読み込んで確認...")
    query = """
    SELECT section, lap_time
    FROM lap_times
    WHERE race_id = ?
    ORDER BY section
    """
    results = db.execute_query(query, (race_id,))

    if results:
        print(f"   ✓ {len(results)} 区間のラップタイムを読み込み")
        print("\n   保存されたラップタイム:")
        for row in results:
            print(f"   - 区間 {row[0]}: {row[1]}秒")
        print()
    else:
        print("   ✗ ラップタイムの読み込みに失敗\n")
        return False

    # 合計タイムの計算（検証）
    total_time = sum(row[1] for row in results)
    print(f"4. 合計タイム: {total_time}秒\n")

    db.disconnect()
    print("=== データベーステスト完了 ===\n")
    print(f"テスト用データベース: {test_db}\n")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("ラップタイム機能テスト")
    print("=" * 60 + "\n")

    # パーステスト
    if not test_lap_times_parsing():
        print("\n❌ パーステストに失敗しました")
        sys.exit(1)

    # データベーステスト
    if not test_lap_times_database():
        print("\n❌ データベーステストに失敗しました")
        sys.exit(1)

    print("=" * 60)
    print("✅ すべてのテストに成功しました！")
    print("=" * 60)
