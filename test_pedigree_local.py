#!/usr/bin/env python3
"""
ローカルのHTMLファイルから血統情報を取得してテストするスクリプト

使用方法:
    python test_pedigree_local.py <html_file> [horse_id]

例:
    python test_pedigree_local.py sample_horse.html 2012100011
"""
import sys
from pathlib import Path

# プロジェクトのパスを追加
sys.path.insert(0, '/home/user/keiba-prediction-claude')

from src.scraper.parser import NetkeibaParser


def test_pedigree_parsing(html_file: str, horse_id: str = "unknown"):
    """
    血統情報のパースをテスト

    Args:
        html_file: HTMLファイルのパス
        horse_id: 馬ID（表示用）
    """
    print(f"\n{'='*60}")
    print(f"🐴 Testing pedigree parsing")
    print(f"{'='*60}\n")
    print(f"📄 HTML file: {html_file}")
    print(f"🆔 Horse ID: {horse_id}\n")

    # HTMLファイルを読み込む
    html_path = Path(html_file)
    if not html_path.exists():
        print(f"❌ Error: File not found: {html_file}")
        return

    print(f"📖 Reading HTML file...")
    html = html_path.read_text(encoding='utf-8')
    print(f"✓ HTML loaded successfully ({len(html)} characters)\n")

    # パースを実行
    print("🔍 Parsing pedigree information...")
    pedigree = NetkeibaParser.parse_horse_pedigree(html, horse_id)

    # 結果を表示
    print(f"\n{'='*60}")
    print("📊 Parsing Results")
    print(f"{'='*60}\n")

    if not pedigree:
        print("❌ No pedigree data found (empty dictionary)")
        return

    # 各項目を表示
    items = [
        ('生年月日', 'birth_date', '📅'),
        ('父', 'sire', '♂'),
        ('母', 'dam', '♀'),
        ('母父', 'damsire', '♂♀')
    ]

    found_count = 0
    for label, key, icon in items:
        value = pedigree.get(key)
        if value:
            print(f"{icon} {label:8s}: {value}")
            found_count += 1
        else:
            print(f"❌ {label:8s}: (not found)")

    print(f"\n{'='*60}")
    print(f"Summary: {found_count}/{len(items)} items found")
    print(f"{'='*60}\n")

    if found_count == len(items):
        print("✅ All pedigree information successfully extracted!")
    elif found_count > 0:
        print("⚠️  Some pedigree information is missing")
        print("\n💡 Troubleshooting:")
        print("   1. Check if the HTML contains the expected elements")
        print("   2. Verify table with class='blood_table' exists")
        print("   3. Verify profile table with summary containing 'プロフィール' exists")
        print("   4. Check parser code: src/scraper/parser.py (lines 460-543)")
    else:
        print("❌ Failed to extract any pedigree information")
        print("\n💡 Troubleshooting:")
        print("   1. Verify this is a horse detail page HTML")
        print("   2. Check HTML encoding (should be UTF-8 or EUC-JP)")
        print("   3. Inspect HTML manually for expected elements")
        print("   4. Check parser code: src/scraper/parser.py (lines 460-543)")

    # 返り値も表示
    print(f"\n🔍 Raw pedigree dictionary:")
    print(f"   {pedigree}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_pedigree_local.py <html_file> [horse_id]")
        print("\nExample:")
        print("  python test_pedigree_local.py sample_horse.html 2012100011")
        print("  python test_pedigree_local.py test_horse_2018105025.html")
        sys.exit(1)

    html_file = sys.argv[1]
    horse_id = sys.argv[2] if len(sys.argv) > 2 else "unknown"

    try:
        test_pedigree_parsing(html_file, horse_id)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
