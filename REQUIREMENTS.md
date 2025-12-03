# 競馬予想GUIアプリ 要件定義書

## 1. プロジェクト概要

### 1.1 目的
機械学習を用いた競馬予想システムの開発。過去のレースデータを収集・分析し、統計的手法により予想を自動化する。

### 1.2 ターゲットユーザー
- 機械学習による競馬予想を行いたいユーザー
- データドリブンな分析と購入戦略を実践したいユーザー

---

## 2. 技術スタック

### 2.1 コア技術
- **プログラミング言語**: Python 3.10+
- **GUIフレームワーク**: PyQt6 (または PySide6)
- **機械学習**: LightGBM, XGBoost, scikit-learn
- **データ処理**: pandas, numpy
- **データ可視化**: matplotlib, seaborn
- **スクレイピング**: requests, BeautifulSoup4 (または selenium)
- **データベース**: SQLite3

### 2.2 推奨ライブラリ
```
PyQt6
pandas
numpy
scikit-learn
lightgbm
xgboost
matplotlib
seaborn
requests
beautifulsoup4
lxml
```

---

## 3. 機能要件

### 3.1 アプリケーション構成
4つの主要タブで構成：

#### 📥 タブ1: データ収集（スクレイピング）
**目的**: db.netkeiba.com から過去レースデータを収集

**機能**:
- スクレイピング対象期間の設定（開始年月〜終了年月）
- スリープ時間の設定（デフォルト: 2-5秒、GUI調整可能）
- 並行処理数の設定
- 進捗状況の表示（プログレスバー、取得済み件数）
- エラーハンドリングとログ表示
- 中断・再開機能

**取得データ項目**:
- **レース情報**: レース名、開催日、競馬場、距離、馬場状態、天気、レースクラス
- **馬情報**: 馬名、年齢、性別、馬体重、馬体重増減、脚質
- **騎手情報**: 騎手名、騎手成績
- **調教師情報**: 調教師名、調教師成績
- **レース結果**: 着順、タイム、通過順位、上がりタイム、オッズ（単勝、複勝、馬連、馬単、3連複、3連単）
- **血統情報**: 父馬、母馬、母父馬
- **調教情報**: 調教タイム、調教コース、調教評価
- **ラップタイム**: 各ハロンのラップ、ペース情報

**出力**:
- SQLiteデータベースに保存
- 取得データのサマリー表示

---

#### 🤖 タブ2: 機械学習トレーニング
**目的**: 収集したデータで機械学習モデルを訓練

**機能**:
- **モデル選択** (ドロップダウン):
  - LightGBM（デフォルト）
  - XGBoost
  - RandomForest
  - （将来的に拡張可能な設計）

- **特徴量設定**:
  - 使用する特徴量の選択（チェックボックス）
  - 自動特徴量エンジニアリング（過去N走の平均成績など）

- **ハイパーパラメータ設定**:
  - 学習率、木の深さ、イテレーション数などをGUIで調整
  - プリセット（軽量/標準/高精度）

- **訓練設定**:
  - 訓練データ期間の指定
  - テストデータ分割比率（例: 80/20）
  - 交差検証の設定（K-Fold）

- **予測対象の選択**:
  - 着順予測（1-3着）
  - 勝率予測
  - 複勝率予測

- **訓練実行**:
  - 進捗表示
  - リアルタイムでの評価指標表示（Accuracy, F1-score, AUC）
  - 特徴量重要度のグラフ表示

**出力**:
- 訓練済みモデルファイル（.pkl）
- 評価レポート（CSV, テキスト）
- 特徴量重要度の可視化

---

#### 📊 タブ3: バックテスト
**目的**: 過去データでモデルの性能を検証

**機能**:
- **バックテスト期間設定**:
  - 開始日〜終了日の指定
  - 対象競馬場の選択

- **購入戦略シミュレーション**:
  - 賭け式の選択（単勝、複勝、馬連、馬単、3連複、3連単）
  - 購入条件（予測確率の閾値、上位N頭など）
  - 賭け金額設定（固定額、比例配分）

- **評価指標**:
  - **ROI (Return on Investment)**: 回収率
  - 的中率
  - 総購入額 vs 総払戻額
  - レース毎の収支推移グラフ

- **結果表示**:
  - レース別の予測結果一覧（テーブル表示）
  - 収支推移グラフ（折れ線グラフ）
  - 競馬場別、クラス別の成績サマリー
  - 混同行列（着順予測の場合）

**出力**:
- バックテストレポート（HTML, PDF）
- 結果データのエクスポート（CSV）

---

#### 🎯 タブ4: 本番予想
**目的**: 未来のレースに対する予想を実行

**機能**:
- **レースデータ取得**:
  - 今週末・当日のレース情報を取得
  - 出走馬一覧の表示

- **予想実行**:
  - 訓練済みモデルを選択（ドロップダウン）
  - 予想を実行ボタン

- **結果表示**:
  - レース毎の予想着順（1-3着）
  - 予測確率の表示
  - 推奨購入馬券の提案（戦略に基づく）
  - オッズ情報の統合表示

- **出力**:
  - 予想結果のエクスポート（CSV, テキスト）
  - 印刷可能なフォーマット

**追加機能**:
- 予想結果の保存と後日の答え合わせ
- 実績トラッキング

---

## 4. 非機能要件

### 4.1 パフォーマンス
- スクレイピング時のIPブロック回避（2-5秒のスリープ、調整可能）
- 大量データ（10年分）の処理に対応
- モデル訓練時間の最適化（特徴量の事前計算）

### 4.2 ユーザビリティ
- 直感的なタブベースのUI
- CSS風スタイリングによるモダンなデザイン
- グラフの視認性の高さ
- エラーメッセージの分かりやすさ

### 4.3 保守性
- モジュール化されたコード設計
- 機械学習モデルの追加が容易な設計（プラグイン方式）
- 設定ファイルによる柔軟な調整

### 4.4 拡張性
- 新しい特徴量の追加が容易
- 新しい機械学習モデルの追加が容易
- データソースの追加（将来的にJRA公式APIなど）

---

## 5. データベース設計

### 5.1 主要テーブル

#### races（レース情報）
```sql
CREATE TABLE races (
    race_id TEXT PRIMARY KEY,
    race_name TEXT,
    date DATE,
    venue TEXT,
    distance INTEGER,
    track_type TEXT,  -- 芝、ダート
    track_condition TEXT,  -- 良、稍重、重、不良
    weather TEXT,
    race_class TEXT,
    prize_money INTEGER
);
```

#### horses（馬情報）
```sql
CREATE TABLE horses (
    horse_id TEXT PRIMARY KEY,
    horse_name TEXT,
    birth_date DATE,
    sex TEXT,
    sire TEXT,  -- 父
    dam TEXT,   -- 母
    damsire TEXT  -- 母父
);
```

#### race_results（レース結果）
```sql
CREATE TABLE race_results (
    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    race_id TEXT,
    horse_id TEXT,
    finishing_position INTEGER,
    jockey_name TEXT,
    trainer_name TEXT,
    horse_weight INTEGER,
    horse_weight_diff INTEGER,
    odds_win REAL,
    odds_place REAL,
    time REAL,
    last_3f REAL,  -- 上がり3ハロン
    passing_order TEXT,  -- 通過順位
    FOREIGN KEY (race_id) REFERENCES races(race_id),
    FOREIGN KEY (horse_id) REFERENCES horses(horse_id)
);
```

#### odds（オッズ情報）
```sql
CREATE TABLE odds (
    odds_id INTEGER PRIMARY KEY AUTOINCREMENT,
    race_id TEXT,
    odds_type TEXT,  -- 馬連、馬単、3連複、3連単
    combination TEXT,  -- 組み合わせ
    odds REAL,
    FOREIGN KEY (race_id) REFERENCES races(race_id)
);
```

#### training（調教情報）
```sql
CREATE TABLE training (
    training_id INTEGER PRIMARY KEY AUTOINCREMENT,
    horse_id TEXT,
    date DATE,
    course TEXT,
    time REAL,
    evaluation TEXT,
    FOREIGN KEY (horse_id) REFERENCES horses(horse_id)
);
```

---

## 6. プロジェクト構成

```
keiba-prediction-app/
├── src/
│   ├── gui/
│   │   ├── main_window.py          # メインウィンドウ
│   │   ├── tabs/
│   │   │   ├── scraping_tab.py     # タブ1: スクレイピング
│   │   │   ├── training_tab.py     # タブ2: トレーニング
│   │   │   ├── backtest_tab.py     # タブ3: バックテスト
│   │   │   └── prediction_tab.py   # タブ4: 本番予想
│   │   └── widgets/                # 共通ウィジェット
│   ├── scraper/
│   │   ├── netkeiba_scraper.py     # スクレイピング処理
│   │   └── parser.py               # HTMLパース処理
│   ├── database/
│   │   ├── db_manager.py           # DB操作
│   │   └── schema.sql              # テーブル定義
│   ├── ml/
│   │   ├── base_model.py           # 抽象基底クラス
│   │   ├── lightgbm_model.py       # LightGBM実装
│   │   ├── xgboost_model.py        # XGBoost実装
│   │   ├── randomforest_model.py   # RandomForest実装
│   │   ├── feature_engineering.py  # 特徴量エンジニアリング
│   │   └── evaluator.py            # 評価指標計算
│   ├── backtest/
│   │   ├── simulator.py            # バックテストシミュレーター
│   │   └── strategy.py             # 購入戦略
│   └── utils/
│       ├── config.py               # 設定管理
│       └── logger.py               # ログ管理
├── data/
│   ├── raw/                        # 生データ
│   ├── processed/                  # 前処理済みデータ
│   └── keiba.db                    # SQLiteデータベース
├── models/                         # 訓練済みモデル
├── logs/                           # ログファイル
├── config/
│   └── settings.json               # アプリ設定
├── requirements.txt
├── REQUIREMENTS.md                 # 本ドキュメント
└── main.py                         # エントリーポイント
```

---

## 7. 開発フェーズ

### Phase 1: 基盤構築
- [x] 要件定義
- [ ] プロジェクト構造の作成
- [ ] データベーススキーマの実装
- [ ] 基本的なGUI骨格（タブ構造）

### Phase 2: データ収集
- [ ] netkeibaスクレイピング機能
- [ ] データパース処理
- [ ] DB保存機能
- [ ] スクレイピングタブUI

### Phase 3: 機械学習
- [ ] 特徴量エンジニアリング
- [ ] ベースモデルクラスの実装
- [ ] LightGBMモデルの実装
- [ ] トレーニングタブUI

### Phase 4: バックテスト
- [ ] バックテストシミュレーター
- [ ] 購入戦略の実装
- [ ] 評価指標の計算
- [ ] バックテストタブUI

### Phase 5: 本番予想
- [ ] 未来レースデータ取得
- [ ] 予想実行機能
- [ ] 結果出力機能
- [ ] 予想タブUI

### Phase 6: 改善・拡張
- [ ] UI/UXの洗練
- [ ] XGBoost, RandomForestの追加
- [ ] パフォーマンス最適化
- [ ] ドキュメント整備

---

## 8. リスクと対策

### 8.1 スクレイピングリスク
**リスク**: db.netkeiba.comからのIPブロック
**対策**:
- 適切なスリープ時間（2-5秒）
- User-Agentの設定
- リトライ機能の実装
- robots.txtの遵守

### 8.2 データ品質リスク
**リスク**: スクレイピングしたデータの欠損・不整合
**対策**:
- データバリデーション機能
- 欠損値の処理戦略
- ログによるエラー追跡

### 8.3 モデル性能リスク
**リスク**: 予測精度が期待に届かない
**対策**:
- 複数モデルの比較
- 特徴量の継続的改善
- バックテストによる事前評価

---

## 9. 今後の拡張可能性

- **リアルタイムデータ取得**: JRA公式APIとの連携
- **ディープラーニング**: LSTMによる時系列予測
- **アンサンブル学習**: 複数モデルの組み合わせ
- **クラウド対応**: AWS/GCP上での実行
- **Web版**: ブラウザからアクセス可能に

---

## 10. 参考情報

- netkeiba.com データベース: https://db.netkeiba.com/
- LightGBM: https://lightgbm.readthedocs.io/
- PyQt6: https://www.riverbankcomputing.com/software/pyqt/

---

**最終更新**: 2025-12-03
**バージョン**: 1.0
