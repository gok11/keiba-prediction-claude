#!/usr/bin/env python3
"""
競馬データ閲覧ツール
データベースに保存されたレース情報を閲覧するためのコマンドラインツール
"""

import sys
import argparse
from datetime import datetime, timedelta
from src.database.db_manager import DatabaseManager


def list_races(db: DatabaseManager, start_date: str = None, end_date: str = None, limit: int = 50):
    """レース一覧を表示"""
    print("\n" + "=" * 100)
    print("レース一覧")
    print("=" * 100)

    if not start_date:
        # デフォルト: 過去30日間
        end = datetime.now()
        start = end - timedelta(days=30)
        start_date = start.strftime('%Y-%m-%d')
        end_date = end.strftime('%Y-%m-%d')

    query = """
    SELECT race_id, date, venue, race_number, race_name, grade, distance, track_type, track_condition
    FROM races
    WHERE date BETWEEN ? AND ?
    ORDER BY date DESC, venue, race_number
    LIMIT ?
    """

    results = db.execute_query(query, (start_date, end_date, limit))

    if not results:
        print(f"\n期間 {start_date} ～ {end_date} のレースデータが見つかりませんでした。")
        return

    print(f"\n期間: {start_date} ～ {end_date} (最新{limit}件)")
    print("-" * 100)
    print(f"{'日付':<12} {'競馬場':<8} {'R':<3} {'レース名':<30} {'グレード':<8} {'距離':<10} {'馬場':<10}")
    print("-" * 100)

    for row in results:
        race_id = row[0]
        date = row[1] if row[1] else '---'
        venue = row[2] if row[2] else '---'
        race_num = row[3] if row[3] else '-'
        race_name = row[4] if row[4] else '---'
        grade = row[5] if row[5] else '---'
        distance = f"{row[6]}m" if row[6] else '---'
        track = f"{row[7]}{row[8]}" if (row[7] and row[8]) else '---'

        print(f"{date:<12} {venue:<8} {race_num:<3} {race_name:<30} {grade:<8} {distance:<10} {track:<10}")

    print("-" * 100)
    print(f"合計: {len(results)} 件")
    print("\n詳細を見るには: python view_data.py race <race_id>")


def show_race_detail(db: DatabaseManager, race_id: str):
    """レース詳細を表示"""
    print("\n" + "=" * 100)
    print(f"レース詳細: {race_id}")
    print("=" * 100)

    # レース基本情報
    query = """
    SELECT race_name, date, venue, race_number, distance, track_type, track_condition,
           weather, race_class, grade, prize_money, track_index, track_comment, race_analysis_comment
    FROM races WHERE race_id = ?
    """
    race = db.execute_query(query, (race_id,))

    if not race:
        print(f"\nレースID {race_id} が見つかりませんでした。")
        return

    race = race[0]
    print(f"\n【レース情報】")
    print(f"  レース名: {race[0]}")
    print(f"  開催日: {race[1]}")
    race_num_str = f"{race[3]}R" if race[3] else ""
    print(f"  競馬場: {race[2]} {race_num_str}")
    print(f"  距離: {race[4]}m {race[5]} {race[6]}")
    print(f"  天気: {race[7]}")
    print(f"  クラス: {race[8]}")
    if race[9]:
        print(f"  グレード: {race[9]}")
    if race[10]:
        print(f"  賞金: {race[10]:,}円")

    # プレミアム情報
    if race[11] is not None or race[12] or race[13]:
        print(f"\n【プレミアム情報】")
        if race[11] is not None:
            print(f"  馬場指数: {race[11]}")
        if race[12]:
            print(f"  馬場コメント: {race[12][:80]}{'...' if len(race[12]) > 80 else ''}")
        if race[13]:
            print(f"  レース分析: {race[13][:80]}{'...' if len(race[13]) > 80 else ''}")

    # ラップタイム
    lap_query = """
    SELECT section, lap_time
    FROM lap_times
    WHERE race_id = ?
    ORDER BY section
    """
    laps = db.execute_query(lap_query, (race_id,))

    if laps:
        print(f"\n【ラップタイム】")
        lap_str = " - ".join([f"{lap[1]:.1f}" for lap in laps])
        total_time = sum([lap[1] for lap in laps])
        print(f"  {lap_str} (合計: {total_time:.1f}秒)")

    # レース結果
    result_query = """
    SELECT rr.finishing_position, rr.bracket_number, rr.horse_number, h.horse_name,
           rr.jockey_name, rr.trainer_name, rr.time, rr.margin, rr.odds_win, rr.popularity,
           rr.horse_weight, rr.horse_weight_diff, rr.last_3f, rr.time_index, rr.remarks
    FROM race_results rr
    LEFT JOIN horses h ON rr.horse_id = h.horse_id
    WHERE rr.race_id = ?
    ORDER BY rr.finishing_position
    """
    results = db.execute_query(result_query, (race_id,))

    if results:
        print(f"\n【レース結果】")
        print("-" * 100)
        print(f"{'着':<4} {'枠':<3} {'馬番':<4} {'馬名':<20} {'騎手':<12} {'タイム':<8} {'着差':<8} {'人気':<4} {'オッズ':<8} {'馬体重':<10}")
        print("-" * 100)

        for row in results:
            pos = row[0] if row[0] else '---'
            bracket = row[1] if row[1] else '-'
            horse_num = row[2] if row[2] else '-'
            horse_name = row[3] if row[3] else '---'
            jockey = row[4] if row[4] else '---'
            time = row[6] if row[6] else '---'
            margin = row[7] if row[7] else '---'
            odds = f"{row[8]:.1f}" if row[8] else '---'
            pop = row[9] if row[9] else '-'
            weight = f"{row[10]}({row[11]:+d})" if row[10] else '---'

            print(f"{pos:<4} {bracket:<3} {horse_num:<4} {horse_name:<20} {jockey:<12} {time:<8} {margin:<8} {pop:<4} {odds:<8} {weight:<10}")

        print("-" * 100)
        print(f"合計: {len(results)} 頭")

    # 払戻金
    payout_query = """
    SELECT payout_type, combination, payout, popularity
    FROM payouts
    WHERE race_id = ?
    ORDER BY
        CASE payout_type
            WHEN '単勝' THEN 1
            WHEN '複勝' THEN 2
            WHEN '枠連' THEN 3
            WHEN '馬連' THEN 4
            WHEN 'ワイド' THEN 5
            WHEN '馬単' THEN 6
            WHEN '3連複' THEN 7
            WHEN '3連単' THEN 8
        END,
        popularity
    """
    payouts = db.execute_query(payout_query, (race_id,))

    if payouts:
        print(f"\n【払戻金】")
        current_type = None
        for row in payouts:
            payout_type = row[0]
            combination = row[1]
            payout = row[2]
            pop = row[3]

            if payout_type != current_type:
                print(f"\n  {payout_type}:")
                current_type = payout_type

            pop_str = f"({pop}番人気)" if pop else ""
            print(f"    {combination} → {payout:,}円 {pop_str}")

    # 注目馬短評
    review_query = """
    SELECT finishing_position, horse_name, review
    FROM horse_short_reviews
    WHERE race_id = ?
    ORDER BY finishing_position
    """
    reviews = db.execute_query(review_query, (race_id,))

    if reviews:
        print(f"\n【注目馬短評】")
        for row in reviews:
            pos = f"{row[0]}着" if row[0] else "---"
            horse_name = row[1]
            review = row[2][:100] + "..." if len(row[2]) > 100 else row[2]
            print(f"\n  {pos}: {horse_name}")
            print(f"    {review}")


def show_horse_history(db: DatabaseManager, horse_id: str, limit: int = 10):
    """馬の過去成績を表示"""
    print("\n" + "=" * 100)
    print(f"馬の過去成績: {horse_id}")
    print("=" * 100)

    # 馬の基本情報
    horse_query = """
    SELECT horse_name, birth_date, sex, sire, dam, damsire
    FROM horses WHERE horse_id = ?
    """
    horse = db.execute_query(horse_query, (horse_id,))

    if not horse:
        print(f"\n馬ID {horse_id} が見つかりませんでした。")
        return

    horse = horse[0]
    print(f"\n【基本情報】")
    print(f"  馬名: {horse[0]}")
    print(f"  生年月日: {horse[1]}")
    print(f"  性別: {horse[2]}")
    print(f"  血統: {horse[3]} × {horse[4]} (母父: {horse[5]})")

    # 過去成績
    history_query = """
    SELECT r.date, r.venue, r.race_name, r.distance, r.track_type, r.track_condition,
           rr.finishing_position, rr.time, rr.jockey_name, rr.popularity, rr.odds_win
    FROM race_results rr
    LEFT JOIN races r ON rr.race_id = r.race_id
    WHERE rr.horse_id = ?
    ORDER BY r.date DESC
    LIMIT ?
    """
    history = db.execute_query(history_query, (horse_id, limit))

    if history:
        print(f"\n【過去成績】(最新{limit}件)")
        print("-" * 100)
        print(f"{'日付':<12} {'競馬場':<8} {'レース名':<25} {'距離':<10} {'馬場':<10} {'着順':<4} {'タイム':<8} {'人気':<4} {'オッズ':<8}")
        print("-" * 100)

        for row in history:
            date = row[0]
            venue = row[1]
            race_name = row[2][:25] if row[2] else '---'
            distance = f"{row[3]}m" if row[3] else '---'
            track = f"{row[4]}{row[5]}" if row[4] else '---'
            pos = row[6] if row[6] else '---'
            time = row[7] if row[7] else '---'
            pop = row[9] if row[9] else '-'
            odds = f"{row[10]:.1f}" if row[10] else '---'

            print(f"{date:<12} {venue:<8} {race_name:<25} {distance:<10} {track:<10} {pos:<4} {time:<8} {pop:<4} {odds:<8}")

        print("-" * 100)
        print(f"合計: {len(history)} 戦")


def show_stats(db: DatabaseManager):
    """データベース統計情報を表示"""
    print("\n" + "=" * 80)
    print("データベース統計情報")
    print("=" * 80)

    tables = [
        ('races', 'レース数'),
        ('horses', '馬数'),
        ('race_results', 'レース結果数'),
        ('payouts', '払戻金記録数'),
        ('lap_times', 'ラップタイム記録数'),
        ('training_details', '調教タイム記録数'),
        ('stable_comments', '厩舎コメント数'),
        ('horse_short_reviews', '注目馬短評数'),
    ]

    print()
    for table_name, description in tables:
        try:
            count_query = f"SELECT COUNT(*) FROM {table_name}"
            result = db.execute_query(count_query)
            count = result[0][0] if result else 0
            print(f"  {description}: {count:,} 件")
        except Exception as e:
            print(f"  {description}: エラー ({e})")

    # 最新/最古のレース日付
    date_query = """
    SELECT MIN(date) as oldest, MAX(date) as newest
    FROM races
    """
    result = db.execute_query(date_query)
    if result and result[0][0]:
        oldest = result[0][0]
        newest = result[0][1]
        print(f"\n  データ期間: {oldest} ～ {newest}")

    # 競馬場別レース数
    venue_query = """
    SELECT venue, COUNT(*) as count
    FROM races
    GROUP BY venue
    ORDER BY count DESC
    """
    venues = db.execute_query(venue_query)
    if venues:
        print(f"\n  【競馬場別レース数】")
        for row in venues:
            print(f"    {row[0]}: {row[1]:,} レース")

    print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description='競馬データ閲覧ツール',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # レース一覧を表示（過去30日間）
  python view_data.py list

  # 期間を指定してレース一覧を表示
  python view_data.py list --start 2015-06-01 --end 2015-06-30

  # レース詳細を表示
  python view_data.py race 201506010101

  # 馬の過去成績を表示
  python view_data.py horse 2012104324

  # データベース統計を表示
  python view_data.py stats
        """
    )

    parser.add_argument('command',
                       choices=['list', 'race', 'horse', 'stats'],
                       help='実行するコマンド')
    parser.add_argument('id', nargs='?', help='レースIDまたは馬ID')
    parser.add_argument('--start', help='開始日 (YYYY-MM-DD)')
    parser.add_argument('--end', help='終了日 (YYYY-MM-DD)')
    parser.add_argument('--limit', type=int, default=50, help='表示件数 (デフォルト: 50)')
    parser.add_argument('--db', default='data/keiba.db', help='データベースパス')

    args = parser.parse_args()

    # データベース接続
    db = DatabaseManager(args.db)
    db.connect()

    try:
        if args.command == 'list':
            list_races(db, args.start, args.end, args.limit)

        elif args.command == 'race':
            if not args.id:
                print("エラー: レースIDを指定してください")
                print("例: python view_data.py race 201506010101")
                sys.exit(1)
            show_race_detail(db, args.id)

        elif args.command == 'horse':
            if not args.id:
                print("エラー: 馬IDを指定してください")
                print("例: python view_data.py horse 2012104324")
                sys.exit(1)
            show_horse_history(db, args.id, args.limit)

        elif args.command == 'stats':
            show_stats(db)

    finally:
        db.disconnect()


if __name__ == '__main__':
    main()
