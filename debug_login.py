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

# フォームのactionを確認し、POST先URLを決定
form_action = form.get('action', '') if form else ''
if form_action:
    if form_action.startswith('http'):
        post_url = form_action
    elif form_action.startswith('/'):
        # 絶対パス
        post_url = f"https://regist.netkeiba.com{form_action}"
    else:
        # 相対パス
        post_url = f"https://regist.netkeiba.com/account/{form_action}"
    print(f"\n  フォームaction: {form_action}")
    print(f"  POST先URL: {post_url}")
else:
    post_url = login_url
    print(f"\n  フォームactionなし、デフォルトURL使用: {post_url}")

print(f"\n  POSTデータ:")
for key, value in login_data.items():
    if key == 'pswd':
        print(f"    {key}: ***")
    else:
        print(f"    {key}: {value}")

try:
    response = session.post(post_url, data=login_data, timeout=30, allow_redirects=True)
    response.encoding = 'euc-jp'
    print(f"\n  ステータスコード: {response.status_code}")
    print(f"  最終URL: {response.url}")

    # リダイレクト履歴を表示
    if response.history:
        print(f"\n  リダイレクト履歴:")
        for idx, hist in enumerate(response.history):
            print(f"    {idx + 1}. {hist.status_code} -> {hist.url}")

    # Cookieを確認
    print(f"\n  取得したCookie:")
    for cookie in session.cookies:
        print(f"    {cookie.name} = {cookie.value[:20]}... (domain: {cookie.domain}, path: {cookie.path})")

    # レスポンスにエラーメッセージがないか確認
    error_patterns = [
        ('ログインページ', 'ログインID' in response.text and 'パスワード' in response.text),
        ('ログイン失敗', 'ログインに失敗' in response.text),
        ('エラー', 'エラー' in response.text and 'ログイン' in response.text),
        ('認証失敗', '認証' in response.text and '失敗' in response.text),
    ]

    for name, found in error_patterns:
        if found:
            print(f"  ⚠️ {name}メッセージを検出")

    # ログイン後のページを保存
    with open('debug_login_response.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    print(f"\n  → debug_login_response.htmlに保存しました")

except Exception as e:
    print(f"  ❌ エラー: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ステップ3: プレミアムページにアクセス
print("\nステップ3: プレミアムページにアクセス")
test_race_url = "https://db.netkeiba.com/race/202408030211/"
try:
    test_response = session.get(test_race_url, timeout=30)
    test_response.encoding = 'euc-jp'
    print(f"  ステータスコード: {test_response.status_code}")

    # プレミアム情報の確認（実際の数値データがあるかをチェック）
    import re

    # 馬場指数の実データを探す（例: "馬場指数 2.5" のようなパターン）
    track_index_pattern = r'馬場指数[^\d]*(\d+\.?\d*)'
    track_index_match = re.search(track_index_pattern, test_response.text)
    has_track_index_data = track_index_match is not None

    # タイム指数の実データを探す
    time_index_pattern = r'タイム指数[^\d]*(\d+\.?\d*)'
    time_index_match = re.search(time_index_pattern, test_response.text)
    has_time_index_data = time_index_match is not None

    # エラーメッセージの確認
    has_premium_error = 'プレミアムサービス' in test_response.text or 'プレミアム会員限定' in test_response.text

    checks = {
        '馬場指数（実データ）': has_track_index_data,
        'タイム指数（実データ）': has_time_index_data,
        'プレミアムエラーメッセージ': has_premium_error,
    }

    print("\n  ページ内容の確認:")
    for key, found in checks.items():
        if 'エラー' in key:
            status = "✅" if not found else "❌"
            print(f"    {status} {key}: {'検出' if found else '未検出'}")
        else:
            status = "✅" if found else "❌"
            print(f"    {status} {key}: {'検出' if found else '未検出'}")
            if found:
                if '馬場指数' in key and track_index_match:
                    print(f"        値: {track_index_match.group(1)}")
                elif 'タイム指数' in key and time_index_match:
                    print(f"        値: {time_index_match.group(1)}")

    # デバッグ用にページを保存
    with open('debug_race_page.html', 'w', encoding='utf-8') as f:
        f.write(test_response.text)
    print("\n  → debug_race_page.htmlに保存しました")

    # デバッグ用に一部を表示
    if has_premium_error:
        print("\n  エラーメッセージ周辺のコンテキスト:")
        error_context = re.search(r'.{50}プレミアム[サービス会員限定]{0,10}.{50}', test_response.text)
        if error_context:
            print(f"    ...{error_context.group(0)}...")

    # 判定
    if has_track_index_data or has_time_index_data:
        print("\n✅ ログイン成功！プレミアム情報の実データにアクセスできます")
    elif has_premium_error:
        print("\n❌ ログイン失敗：プレミアム会員限定メッセージが表示されています")
    else:
        print("\n⚠️ 不明：プレミアム情報が見つかりませんが、エラーメッセージもありません")

except Exception as e:
    print(f"  ❌ エラー: {e}")
    sys.exit(1)

print("\n=== デバッグ完了 ===")
