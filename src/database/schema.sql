-- 競馬予想アプリ データベーススキーマ

-- レース情報テーブル
CREATE TABLE IF NOT EXISTS races (
    race_id TEXT PRIMARY KEY,
    race_name TEXT NOT NULL,
    date DATE NOT NULL,
    venue TEXT NOT NULL,
    distance INTEGER NOT NULL,
    track_type TEXT NOT NULL CHECK (track_type IN ('芝', 'ダート', '障害')),
    track_condition TEXT CHECK (track_condition IN ('良', '稍重', '重', '不良')),
    weather TEXT,
    race_class TEXT,
    prize_money INTEGER,
    grade TEXT,  -- G1, G2, G3, など
    race_number INTEGER,
    start_time TIME,
    -- プレミアム情報
    track_index INTEGER,  -- 馬場指数
    track_comment TEXT,  -- 馬場コメント
    race_analysis_comment TEXT,  -- レース分析コメント
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 馬情報テーブル
CREATE TABLE IF NOT EXISTS horses (
    horse_id TEXT PRIMARY KEY,
    horse_name TEXT NOT NULL,
    birth_date DATE,
    sex TEXT CHECK (sex IN ('牡', '牝', 'セ')),
    sire TEXT,  -- 父
    dam TEXT,   -- 母
    damsire TEXT,  -- 母父
    sire_sire TEXT,  -- 父父
    sire_dam TEXT,   -- 父母
    dam_dam TEXT,    -- 母母
    breeder TEXT,  -- 生産者
    owner TEXT,  -- 馬主
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 騎手情報テーブル
CREATE TABLE IF NOT EXISTS jockeys (
    jockey_id TEXT PRIMARY KEY,
    jockey_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 調教師情報テーブル
CREATE TABLE IF NOT EXISTS trainers (
    trainer_id TEXT PRIMARY KEY,
    trainer_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- レース結果テーブル
CREATE TABLE IF NOT EXISTS race_results (
    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    race_id TEXT NOT NULL,
    horse_id TEXT NOT NULL,
    finishing_position INTEGER,
    bracket_number INTEGER,  -- 枠番
    horse_number INTEGER,  -- 馬番
    jockey_id TEXT,
    jockey_name TEXT,
    jockey_weight REAL,  -- 斤量
    trainer_id TEXT,
    trainer_name TEXT,
    horse_weight INTEGER,
    horse_weight_diff INTEGER,
    odds_win REAL,  -- 単勝オッズ
    odds_place REAL,  -- 複勝オッズ
    popularity INTEGER,  -- 人気
    time REAL,  -- タイム（秒）
    margin TEXT,  -- 着差
    last_3f REAL,  -- 上がり3ハロン
    passing_order TEXT,  -- 通過順位（コーナー毎）
    running_style TEXT,  -- 脚質
    disqualification TEXT,  -- 失格・除外情報
    -- プレミアム情報
    time_index INTEGER,  -- タイム指数
    remarks TEXT,  -- 備考（出遅れなど）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (race_id) REFERENCES races(race_id),
    FOREIGN KEY (horse_id) REFERENCES horses(horse_id),
    FOREIGN KEY (jockey_id) REFERENCES jockeys(jockey_id),
    FOREIGN KEY (trainer_id) REFERENCES trainers(trainer_id)
);

-- オッズ情報テーブル
CREATE TABLE IF NOT EXISTS odds (
    odds_id INTEGER PRIMARY KEY AUTOINCREMENT,
    race_id TEXT NOT NULL,
    odds_type TEXT NOT NULL CHECK (odds_type IN ('単勝', '複勝', '馬連', '馬単', 'ワイド', '3連複', '3連単')),
    combination TEXT NOT NULL,  -- 組み合わせ（例: "1-3-5"）
    odds REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (race_id) REFERENCES races(race_id)
);

-- 払戻金テーブル
CREATE TABLE IF NOT EXISTS payouts (
    payout_id INTEGER PRIMARY KEY AUTOINCREMENT,
    race_id TEXT NOT NULL,
    payout_type TEXT NOT NULL CHECK (payout_type IN ('単勝', '複勝', '枠連', '馬連', '馬単', 'ワイド', '3連複', '3連単')),
    combination TEXT NOT NULL,
    payout INTEGER,  -- 払戻金（100円あたり）
    popularity INTEGER,  -- 人気
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (race_id) REFERENCES races(race_id)
);

-- 調教情報テーブル
CREATE TABLE IF NOT EXISTS training (
    training_id INTEGER PRIMARY KEY AUTOINCREMENT,
    horse_id TEXT NOT NULL,
    race_id TEXT,  -- 対象レース
    date DATE NOT NULL,
    course TEXT,  -- 調教コース
    distance INTEGER,
    time REAL,  -- タイム
    evaluation TEXT,  -- 評価（A, B, C など）
    type TEXT,  -- 調教タイプ（強め、馬なりなど）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (horse_id) REFERENCES horses(horse_id),
    FOREIGN KEY (race_id) REFERENCES races(race_id)
);

-- 血統情報詳細テーブル
CREATE TABLE IF NOT EXISTS pedigree (
    pedigree_id INTEGER PRIMARY KEY AUTOINCREMENT,
    horse_id TEXT NOT NULL,
    generation INTEGER NOT NULL,  -- 世代（1:父母, 2:祖父母, 3:曾祖父母...）
    position TEXT NOT NULL,  -- 位置（father, mother, father_father, father_mother...）
    ancestor_id TEXT,
    ancestor_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (horse_id) REFERENCES horses(horse_id)
);

-- ラップタイム情報テーブル
CREATE TABLE IF NOT EXISTS lap_times (
    lap_id INTEGER PRIMARY KEY AUTOINCREMENT,
    race_id TEXT NOT NULL,
    section INTEGER NOT NULL,  -- 区間（200m, 400m, 600m...）
    lap_time REAL,  -- ラップタイム
    pace REAL,  -- ペース（累積時間）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (race_id) REFERENCES races(race_id)
);

-- 予想結果保存テーブル
CREATE TABLE IF NOT EXISTS predictions (
    prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    race_id TEXT NOT NULL,
    horse_id TEXT NOT NULL,
    model_name TEXT NOT NULL,
    predicted_position INTEGER,
    probability REAL,  -- 予測確率
    predicted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (race_id) REFERENCES races(race_id),
    FOREIGN KEY (horse_id) REFERENCES horses(horse_id)
);

-- バックテスト結果テーブル
CREATE TABLE IF NOT EXISTS backtest_results (
    backtest_id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    strategy TEXT NOT NULL,
    total_races INTEGER,
    total_bets INTEGER,
    total_cost INTEGER,
    total_return INTEGER,
    roi REAL,
    hit_rate REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- バックテスト詳細テーブル
CREATE TABLE IF NOT EXISTS backtest_details (
    detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
    backtest_id INTEGER NOT NULL,
    race_id TEXT NOT NULL,
    bet_type TEXT NOT NULL,
    bet_combination TEXT NOT NULL,
    bet_amount INTEGER,
    payout INTEGER,
    profit INTEGER,
    FOREIGN KEY (backtest_id) REFERENCES backtest_results(backtest_id),
    FOREIGN KEY (race_id) REFERENCES races(race_id)
);

-- 調教タイム詳細テーブル（プレミアム機能）
CREATE TABLE IF NOT EXISTS training_details (
    training_detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
    horse_id TEXT NOT NULL,
    race_id TEXT NOT NULL,  -- 対象レース
    training_date DATE NOT NULL,
    course TEXT,  -- コース（美坂、南W、栗坂など）
    track_condition TEXT,  -- 馬場状態（良、稍、重、不良）
    rider TEXT,  -- 乗り役（騎手名、助手など）
    time_6f REAL,  -- 6Fタイム（秒）
    time_5f REAL,  -- 5Fタイム（秒）
    time_4f REAL,  -- 4Fタイム（秒）
    time_3f REAL,  -- 3Fタイム（秒）
    time_1f REAL,  -- 1Fタイム（秒）
    position INTEGER,  -- 併せ馬での位置
    intensity TEXT,  -- 脚色（強め、馬也など）
    evaluation_text TEXT,  -- 評価テキスト（態勢整う、順調など）
    evaluation_grade TEXT,  -- 評価グレード（A, B, C など）
    parallel_info TEXT,  -- 併せ馬情報
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (horse_id) REFERENCES horses(horse_id),
    FOREIGN KEY (race_id) REFERENCES races(race_id)
);

-- 厩舎コメントテーブル（プレミアム機能）
CREATE TABLE IF NOT EXISTS stable_comments (
    comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    horse_id TEXT NOT NULL,
    race_id TEXT NOT NULL,  -- 対象レース
    comment TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (horse_id) REFERENCES horses(horse_id),
    FOREIGN KEY (race_id) REFERENCES races(race_id)
);

-- 注目馬短評テーブル（プレミアム機能）
CREATE TABLE IF NOT EXISTS horse_short_reviews (
    review_id INTEGER PRIMARY KEY AUTOINCREMENT,
    race_id TEXT NOT NULL,
    horse_id TEXT NOT NULL,
    horse_name TEXT NOT NULL,
    finishing_position INTEGER,  -- 着順
    review TEXT NOT NULL,  -- 短評
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (race_id) REFERENCES races(race_id),
    FOREIGN KEY (horse_id) REFERENCES horses(horse_id)
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_races_date ON races(date);
CREATE INDEX IF NOT EXISTS idx_races_venue ON races(venue);
CREATE INDEX IF NOT EXISTS idx_race_results_race_id ON race_results(race_id);
CREATE INDEX IF NOT EXISTS idx_race_results_horse_id ON race_results(horse_id);
CREATE INDEX IF NOT EXISTS idx_odds_race_id ON odds(race_id);
CREATE INDEX IF NOT EXISTS idx_training_horse_id ON training(horse_id);
CREATE INDEX IF NOT EXISTS idx_training_date ON training(date);
CREATE INDEX IF NOT EXISTS idx_predictions_race_id ON predictions(race_id);
CREATE INDEX IF NOT EXISTS idx_backtest_results_model ON backtest_results(model_name);
CREATE INDEX IF NOT EXISTS idx_training_details_horse_id ON training_details(horse_id);
CREATE INDEX IF NOT EXISTS idx_training_details_race_id ON training_details(race_id);
CREATE INDEX IF NOT EXISTS idx_stable_comments_horse_id ON stable_comments(horse_id);
CREATE INDEX IF NOT EXISTS idx_stable_comments_race_id ON stable_comments(race_id);
CREATE INDEX IF NOT EXISTS idx_horse_short_reviews_race_id ON horse_short_reviews(race_id);
CREATE INDEX IF NOT EXISTS idx_horse_short_reviews_horse_id ON horse_short_reviews(horse_id);
