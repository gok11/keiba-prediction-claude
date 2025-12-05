"""
既存の馬データに祖父母情報を追加するスクリプト
"""

import sys
from src.database.db_manager import DatabaseManager
from src.scraper.netkeiba_scraper import NetkeibaScraper
import time

def update_existing_horses():
    """既存の馬データに祖父母情報を追加"""
    db_manager = DatabaseManager()
    scraper = NetkeibaScraper(db_manager=db_manager)

    # 祖父母情報がない馬を取得
    query = """
    SELECT horse_id, horse_name
    FROM horses
    WHERE (sire_sire IS NULL OR sire_dam IS NULL OR dam_dam IS NULL)
    AND sire IS NOT NULL
    """

    horses = db_manager.execute_query(query)
    total = len(horses)

    print(f"祖父母情報を更新する馬: {total}頭")

    if total == 0:
        print("更新する馬がありません")
        return

    updated = 0
    failed = 0

    for idx, horse in enumerate(horses, 1):
        horse_id = horse[0]
        horse_name = horse[1]

        print(f"[{idx}/{total}] {horse_name} ({horse_id}) の祖父母情報を取得中...")

        try:
            # 血統情報を再取得
            pedigree = scraper.scrape_horse_pedigree(horse_id)

            if pedigree:
                sire_sire = pedigree.get('sire_sire')
                sire_dam = pedigree.get('sire_dam')
                dam_dam = pedigree.get('dam_dam')

                # 祖父母情報を更新
                update_query = """
                UPDATE horses
                SET sire_sire = ?, sire_dam = ?, dam_dam = ?
                WHERE horse_id = ?
                """
                db_manager.execute_update(update_query, (sire_sire, sire_dam, dam_dam, horse_id))

                print(f"  ✓ 更新完了: 父父={sire_sire}, 父母={sire_dam}, 母母={dam_dam}")
                updated += 1
            else:
                print(f"  ✗ 血統情報の取得に失敗")
                failed += 1

        except Exception as e:
            print(f"  ✗ エラー: {e}")
            failed += 1

        # リクエスト間隔を空ける
        if idx < total:
            time.sleep(2)

    print(f"\n完了: 更新={updated}頭, 失敗={failed}頭")

if __name__ == "__main__":
    update_existing_horses()
