#!/usr/bin/env python3
"""
単一の馬IDから血統情報を取得してテストするスクリプト

使用方法:
    python test_pedigree.py <horse_id>

例:
    python test_pedigree.py 2012100011  # sample_horse.htmlの馬
"""
import sys
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトのパスを追加
sys.path.insert(0, '/home/user/keiba-prediction-claude')

from src.scraper.parser import NetkeibaParser

# .envファイルを読み込む
load_dotenv()


def fetch_horse_page(horse_id: str, save_html: bool = True):
    """
    馬の血統詳細ページを取得

    Args:
        horse_id: 馬ID
        save_html: HTMLを保存するか

    Returns:
        HTMLコンテンツ
    """
    # 血統詳細ページを取得（静的HTMLで5代血統表が含まれる）
    url = f"https://db.netkeiba.com/horse/ped/{horse_id}/"

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
    })

    # プレミアムログイン（オプション）
    login_id = os.getenv('NETKEIBA_LOGIN_ID')
    password = os.getenv('NETKEIBA_PASSWORD')

    if login_id and password:
        print(f"🔐 Logging in with ID: {login_id}")
        login_url = "https://regist.netkeiba.com/account/?pid=login"
        login_page = session.get(login_url)

        login_data = {
            'login_id': login_id,
            'pswd': password
        }
        response = session.post(login_url, data=login_data, allow_redirects=True)

        if 'データベース' in response.text:
            print("✓ Login successful")
        else:
            print("⚠ Login might have failed (continuing anyway)")
    else:
        print("ℹ No login credentials found in .env")

    print(f"\n📡 Fetching horse page: {url}")
    response = session.get(url)
    response.encoding = 'EUC-JP'

    if response.status_code != 200:
        print(f"❌ Error: HTTP {response.status_code}")
        return None

    html_content = response.text

    # HTMLを保存
    if save_html:
        output_file = Path(f'test_horse_{horse_id}.html')
        # charset指定を修正
        html_to_save = html_content.replace('charset=euc-jp', 'charset=utf-8')
        html_to_save = html_to_save.replace('charset=EUC-JP', 'charset=utf-8')
        output_file.write_text(html_to_save, encoding='utf-8')
        print(f"💾 Saved HTML to {output_file}")

    return html_content


def test_pedigree_parsing(horse_id: str):
    """
    血統情報のパースをテスト

    Args:
        horse_id: 馬ID
    """
    print(f"\n{'='*60}")
    print(f"🐴 Testing pedigree parsing for horse ID: {horse_id}")
    print(f"{'='*60}\n")

    # 馬詳細ページを取得
    html = fetch_horse_page(horse_id)
    if not html:
        print("❌ Failed to fetch horse page")
        return

    print(f"✓ HTML fetched successfully ({len(html)} characters)\n")

    # パースを実行
    print("🔍 Parsing pedigree information...")
    pedigree = NetkeibaParser.parse_horse_pedigree(html, horse_id)

    # 結果を表示
    print(f"\n{'='*60}")
    print("📊 Parsing Results")
    print(f"{'='*60}\n")

    if not pedigree:
        print("❌ No pedigree data found")
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
    else:
        print("❌ Failed to extract any pedigree information")

    # デバッグ情報
    print("\n💡 Debug info:")
    print(f"   - HTML file saved as: test_horse_{horse_id}.html")
    print(f"   - You can inspect it with a browser")
    print(f"   - Parser code: src/scraper/parser.py (lines 460-543)")


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_pedigree.py <horse_id>")
        print("\nExample:")
        print("  python test_pedigree.py 2012100011  # ディアクリューソス")
        print("  python test_pedigree.py 2018105025  # sample_horse.htmlの馬")
        sys.exit(1)

    horse_id = sys.argv[1]

    try:
        test_pedigree_parsing(horse_id)
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
