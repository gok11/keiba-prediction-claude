# プレミアム機能実装ガイド

## 概要

netkeiba.comプレミアム会員向けの機能を実装しました。ログイン認証を行い、プレミアム限定の数値データとテキストデータを自動取得してデータベースに保存します。

## 実装された機能

### 1. 自動ログイン機能
- `.env`ファイルから認証情報を読み込み
- スクレイパー初期化時に自動ログイン
- セッション維持によりログイン状態を保持

### 2. プレミアム数値データ
レース詳細ページから以下の数値データを取得：

| データ項目 | テーブル | カラム | 説明 |
|-----------|---------|--------|------|
| 馬場指数 | races | track_index | 馬場の速さを示す指数 |
| タイム指数 | race_results | time_index | 各馬のタイム指数 |

### 3. プレミアムテキストデータ
レース詳細ページから以下のテキストデータを取得：

| データ項目 | テーブル | カラム | 説明 |
|-----------|---------|--------|------|
| 馬場コメント | races | track_comment | 馬場状態の詳細説明 |
| レース分析コメント | races | race_analysis_comment | レース展開の分析 |
| 備考 | race_results | remarks | 出遅れなどの備考 |
| 注目馬短評 | horse_short_reviews | review | レース後の短評（1-3着馬など） |

### 4. 調教情報（オプション）
馬詳細ページから以下の調教データを取得（`fetch_premium_training=True`時）：

| データ項目 | テーブル | カラム | 説明 |
|-----------|---------|--------|------|
| 調教タイム | training_details | time_6f, time_5f, time_4f, time_3f, time_1f | 各区間のタイム |
| 調教コース | training_details | course | 美坂、南W、栗坂など |
| 馬場状態 | training_details | track_condition | 良、稍、重、不良 |
| 脚色 | training_details | intensity | 強め、馬也など |
| 評価 | training_details | evaluation_grade | A, B, C など |
| 厩舎コメント | stable_comments | comment | 厩舎からのコメント |

## セットアップ方法

### 1. 認証情報の設定

`.env`ファイルをプロジェクトルートに作成し、以下の内容を記述：

```bash
NETKEIBA_USERNAME=your_email@example.com
NETKEIBA_PASSWORD=your_password
```

**注意**: `.env`ファイルは`.gitignore`に含まれており、リポジトリにコミットされません。

### 2. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

必要なパッケージ：
- `beautifulsoup4`: HTMLパース
- `lxml`: パーサー
- `requests`: HTTP通信
- `python-dotenv`: 環境変数読み込み

### 3. データベースの初期化

既存のデータベースを使用する場合、スキーマが自動的に更新されます。新規の場合は自動的に初期化されます。

## 使用方法

### 基本的な使い方（プレミアム情報のみ）

```python
from src.scraper.netkeiba_scraper import NetkeibaScraper
from src.database.db_manager import DatabaseManager

# データベースとスクレイパーを初期化
db_manager = DatabaseManager()
scraper = NetkeibaScraper(db_manager)

# 自動的にログインされる（.envに認証情報がある場合）
# is_logged_in=Trueの場合、プレミアム情報が自動取得される

# 単一レースをスクレイピング
race_id = "202408030211"
scraper.scrape_race(race_id)

# 取得されるデータ:
# - レース基本情報 + 馬場指数 + 馬場コメント + レース分析
# - レース結果 + タイム指数 + 備考
# - 注目馬短評（1-3着馬など）
```

### 調教情報も取得する場合

```python
# fetch_premium_training=Trueで調教情報も取得
# ※各馬ごとに追加リクエストが発生するため時間がかかります
scraper.scrape_race(race_id, fetch_premium_training=True)

# 取得されるデータ:
# - 基本プレミアム情報（上記）
# - 調教タイム詳細（各馬ごと）
# - 厩舎コメント（各馬ごと）
```

### 期間指定でスクレイピング

```python
from datetime import datetime

start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 12, 31)

# プレミアム情報は自動的に取得される
scraper.scrape_date_range(start_date, end_date)
```

## テスト

プレミアム機能のテストスクリプトを用意しています：

```bash
python test_premium_features.py
```

テスト内容：
1. `testrace.html`からのプレミアム情報パーステスト
2. データベースへの保存テスト
3. データ整合性の確認

## データベーススキーマ

### racesテーブルへの追加カラム

```sql
track_index INTEGER,              -- 馬場指数
track_comment TEXT,               -- 馬場コメント
race_analysis_comment TEXT        -- レース分析コメント
```

### race_resultsテーブルへの追加カラム

```sql
time_index INTEGER,               -- タイム指数
remarks TEXT                      -- 備考
```

### 新規テーブル

#### training_details（調教タイム詳細）
```sql
CREATE TABLE training_details (
    training_detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
    horse_id TEXT NOT NULL,
    race_id TEXT NOT NULL,
    training_date DATE NOT NULL,
    course TEXT,                  -- コース
    track_condition TEXT,         -- 馬場状態
    rider TEXT,                   -- 乗り役
    time_6f REAL,                 -- 6Fタイム
    time_5f REAL,                 -- 5Fタイム
    time_4f REAL,                 -- 4Fタイム
    time_3f REAL,                 -- 3Fタイム
    time_1f REAL,                 -- 1Fタイム
    position INTEGER,             -- 併せ馬での位置
    intensity TEXT,               -- 脚色
    evaluation_text TEXT,         -- 評価テキスト
    evaluation_grade TEXT,        -- 評価グレード
    parallel_info TEXT,           -- 併せ馬情報
    ...
);
```

#### stable_comments（厩舎コメント）
```sql
CREATE TABLE stable_comments (
    comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    horse_id TEXT NOT NULL,
    race_id TEXT NOT NULL,
    comment TEXT NOT NULL,
    ...
);
```

#### horse_short_reviews（注目馬短評）
```sql
CREATE TABLE horse_short_reviews (
    review_id INTEGER PRIMARY KEY AUTOINCREMENT,
    race_id TEXT NOT NULL,
    horse_id TEXT NOT NULL,
    horse_name TEXT NOT NULL,
    finishing_position INTEGER,
    review TEXT NOT NULL,
    ...
);
```

## パフォーマンスに関する注意

### リクエスト数

1. **基本プレミアム情報**: 追加リクエストなし
   - レース詳細ページから全て取得

2. **調教情報取得時**: 大幅に増加
   - 各馬ごとに2リクエスト（調教タイム + 厩舎コメント）
   - 例: 16頭立てのレース = 32追加リクエスト

### 推奨設定

```python
# 大量のレースをスクレイピングする場合
# 調教情報は必要な場合のみ取得
scraper.scrape_race(race_id, fetch_premium_training=False)  # デフォルト

# 特定の重要レースのみ詳細データを取得
if is_important_race(race_id):
    scraper.scrape_race(race_id, fetch_premium_training=True)
```

## ログの確認

プレミアム機能のログは以下のように出力されます：

```
INFO: netkeiba.comにログイン中...
INFO: ログイン成功
DEBUG: Parsed premium race info for 202408030211
INFO: Saved 16 results, 8 payouts, 4 reviews for race 202408030211
```

調教情報取得時：
```
DEBUG: Saved 5 training records for horse 2019103456
DEBUG: Saved stable comment for horse 2019103456
INFO: Saved 16 results, 8 payouts, 4 reviews (with training data) for race 202408030211
```

## トラブルシューティング

### ログインできない

1. `.env`ファイルが正しい場所にあるか確認
2. 認証情報が正しいか確認
3. netkeiba.comが正常にアクセスできるか確認

```python
scraper.is_logged_in  # Trueならログイン成功
```

### プレミアム情報が取得できない

1. ログインが成功しているか確認
2. 対象ページがプレミアム限定かどうか確認
3. HTMLの構造が変更されていないか確認（パーサーの更新が必要な場合あり）

### データが保存されない

1. データベーススキーマが最新か確認
2. エラーログを確認
3. テストスクリプトを実行して動作確認

```bash
python test_premium_features.py
```

## 今後の拡張

### 自然言語処理での活用

テキストデータ（馬場コメント、レース分析、短評、厩舎コメント）は以下の手法で活用可能：

1. **BERT等の事前学習モデル**
   - 文脈を考慮した特徴抽出
   - 競馬ドメインでのファインチューニング

2. **TF-IDF + 機械学習**
   - キーワード抽出
   - 重要単語の重み付け

3. **感情分析**
   - ポジティブ/ネガティブ評価
   - 期待度の定量化

4. **キーワード抽出**
   - 「出遅れ」「好位」「不利」などの重要フラグ
   - レース展開の特徴抽出

### ラップタイムの実装

現在未実装の機能：
- `lap_times`テーブルは定義済み
- パーサーの実装が必要
- HTMLからラップタイムデータを抽出

## まとめ

プレミアム機能により、以下のデータが自動取得可能になりました：

✅ **数値データ**: 馬場指数、タイム指数
✅ **テキストデータ**: 馬場コメント、レース分析、備考、注目馬短評
✅ **調教データ**: 調教タイム、厩舎コメント（オプション）

これらのデータを活用することで、より精度の高い予想モデルの構築が可能になります。
