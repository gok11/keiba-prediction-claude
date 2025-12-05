"""
ログイン処理のデバッグスクリプト
実際のHTMLを確認して、必要なフィールドを特定する
"""

import requests
import sys
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# .envファイルから認証情報を読み込み
load_dotenv()
username = os.getenv('NETKEIBA_USERNAME')
password = os.getenv('NETKEIBA_PASSWORD')

if not username or not password:
    print("❌ エラー: .envファイルにNETKEIBA_USERNAMEとNETKEIBA_PASSWORDが設定されていません")
    sys.exit(1)

print("=== ログイン処理のデバッグ ===\n")
print(f"認証情報:")
print(f"  ユーザー名: {username[:3]}***")
print(f"  パスワード: ***\n")

# セッションを作成
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
})

# ステップ1: ログインページにアクセス
print("ステップ1: ログインページにアクセス")
login_url = "https://regist.netkeiba.com/account/?pid=login"
try:
    login_page = session.get(login_url, timeout=30)
    login_page.encoding = 'euc-jp'
    print(f"  ステータスコード: {login_page.status_code}")
    print(f"  リダイレクト先: {login_page.url}")

    # HTMLをパースして、ログインフォームを確認
    soup = BeautifulSoup(login_page.text, 'html.parser')

    # すべてのフォームを検出
    all_forms = soup.find_all('form')
    print(f"\n  検出されたフォーム数: {len(all_forms)}")

    # ログインフォームを探す（login_idまたはpswdを含むフォーム）
    login_form = None
    for idx, form in enumerate(all_forms):
        print(f"\n  フォーム #{idx + 1}:")
        print(f"    action: {form.get('action', 'なし')}")
        print(f"    method: {form.get('method', 'なし')}")

        inputs = form.find_all('input')
        input_names = [inp.get('name', '') for inp in inputs]
        print(f"    inputs: {', '.join(filter(None, input_names))}")

        # login_idやpswdを含むフォームをログインフォームとする
        if 'login_id' in input_names or 'pswd' in input_names:
            login_form = form
            print(f"    → これがログインフォームです！")

    # ページの一部を保存
    with open('debug_login_page.html', 'w', encoding='utf-8') as f:
        f.write(login_page.text)
    print(f"\n  → debug_login_page.htmlに保存しました")

    if not login_form:
        print("\n  ❌ ログインフォームが見つかりません")
        print("  → debug_login_page.htmlを確認してください")
        sys.exit(1)

    form = login_form

except Exception as e:
    print(f"  ❌ エラー: {e}")
    sys.exit(1)

# ステップ2: ログイン情報をPOST
print("\nステップ2: ログイン情報をPOST")
login_data = {
    'login_id': username,
    'pswd': password,
}

# フォームからhiddenフィールドを抽出
if form:
    for inp in form.find_all('input', {'type': 'hidden'}):
        name = inp.get('name')
        value = inp.get('value', '')
        if name:
            login_data[name] = value
            print(f"  追加: {name} = {value[:20] if value else ''}")

print(f"\n  POSTデータ:")
for key, value in login_data.items():
    if key == 'pswd':
        print(f"    {key}: ***")
    else:
        print(f"    {key}: {value}")

try:
    response = session.post(login_url, data=login_data, timeout=30, allow_redirects=True)
    response.encoding = 'euc-jp'
    print(f"\n  ステータスコード: {response.status_code}")
    print(f"  最終URL: {response.url}")

    # Cookieを確認
    print(f"\n  取得したCookie:")
    for cookie in session.cookies:
        print(f"    {cookie.name} = {cookie.value[:20]}...")

    # レスポンスにエラーメッセージがないか確認
    if 'ログインID' in response.text and 'パスワード' in response.text:
        print("  ⚠️ まだログインページにいる可能性があります")
    if 'ログインに失敗' in response.text or 'エラー' in response.text:
        print("  ❌ ログインエラーメッセージを検出")

except Exception as e:
    print(f"  ❌ エラー: {e}")
    sys.exit(1)

# ステップ3: プレミアムページにアクセス
print("\nステップ3: プレミアムページにアクセス")
test_race_url = "https://db.netkeiba.com/race/202408030211/"
try:
    test_response = session.get(test_race_url, timeout=30)
    test_response.encoding = 'euc-jp'
    print(f"  ステータスコード: {test_response.status_code}")

    # プレミアム情報の確認
    checks = {
        '馬場指数': '馬場指数' in test_response.text,
        'タイム指数': 'タイム指数' in test_response.text,
        'プレミアムサービス': 'プレミアムサービス' in test_response.text,
        'プレミアム会員限定': 'プレミアム会員限定' in test_response.text,
    }

    print("\n  ページ内容の確認:")
    for key, found in checks.items():
        status = "✅" if (found and '指数' in key) or (not found and 'プレミアム' in key) else "❌"
        print(f"    {status} {key}: {'検出' if found else '未検出'}")

    # デバッグ用にページを保存
    with open('debug_race_page.html', 'w', encoding='utf-8') as f:
        f.write(test_response.text)
    print("\n  → debug_race_page.htmlに保存しました")

    # 判定
    if checks['馬場指数'] or checks['タイム指数']:
        print("\n✅ ログイン成功！プレミアム情報にアクセスできます")
    elif checks['プレミアムサービス'] or checks['プレミアム会員限定']:
        print("\n❌ ログイン失敗：プレミアム会員限定メッセージが表示されています")
    else:
        print("\n⚠️ 不明：プレミアム情報が見つかりませんが、エラーメッセージもありません")

except Exception as e:
    print(f"  ❌ エラー: {e}")
    sys.exit(1)

print("\n=== デバッグ完了 ===")
