# テクゼロン 人財駆動型・企業再興プラットフォーム

> 市場を入力 → AI分析 → 課題発見 → 解決策生成 → リーンキャンバス → 最適チーム編成

株式会社テクゼロン（産業機械製造）の社内新規事業創出を支援するAIプラットフォームです。
4人チームの学習用プロジェクトとして開発しています。

**デプロイ URL:** https://business-revival-platform-v2-6ikrkm5mx4tep3dqd6gnls.streamlit.app/

---

## アプリのフロー（6ステップ）

```
① 市場・ターゲット入力
       ↓
② 市場分析（PEST分析 + 5つの力分析）を AI が実行
       ↓
③ AIが課題を10個生成 → 納得するまで何度でも再生成可能
       ↓  ユーザーが1つ選択
④ AIが解決策を10個生成（5軸スコアリング付き） → 再生成可能
       ↓  ユーザーが1つ選択
⑤ リーンキャンバス（9ブロック）を AI が自動生成
       ↓
⑥ 選んだ解決策に最適な4人チームを社内DBから選抜して表示
```

---

## セットアップ手順

### 1. リポジトリをクローン

```bash
git clone https://github.com/terry-tech0/business-revival-platform.git
cd business-revival-platform
```

### 2. 依存パッケージをインストール

```bash
pip install -r requirements.txt
```

### 3. 環境変数を設定

`.env` ファイルをプロジェクト直下に作成し、OpenAI API キーを記入してください。

```
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxx
```

> **注意:** `.env` ファイルは `.gitignore` に含まれています。絶対にGitにコミットしないでください。

### 4. アプリを起動

```bash
streamlit run app.py
```

初回起動時にダミー社員データ（20名分）が自動で投入されます。

---

## 技術スタック

| レイヤー | 技術 |
|---------|------|
| フロントエンド | Streamlit |
| AI ロジック | OpenAI API (GPT-4o) |
| データベース | SQLite3 |
| 環境変数管理 | python-dotenv |

---

## チーム役割分担

| 担当 | メンバー | 担当ファイル |
|------|---------|------------|
| AI API（クローラー） | テリー | `prompts.py`, `ai_engine.py` |
| フロントエンド | わーちゃん | `app.py` |
| データベース | のずちゃん | `schema.sql`, `seed_data.py`, `database.py` |
| ランキング | みっきー | `matching.py` |

---

## ディレクトリ構成

```
business-revival-platform/
├── .env                  # OpenAI APIキー（Git管理外）
├── .gitignore
├── README.md             # ← このファイル
├── CLAUDE.md             # プロジェクト定義書（Claude Code用）
├── SKILLS.md             # 必要スキル一覧
├── requirements.txt      # Python依存パッケージ
│
├── app.py                # Streamlit UI           【わーちゃん】
├── prompts.py            # AIプロンプトテンプレート  【テリー】
├── ai_engine.py          # OpenAI API連携          【テリー】
├── matching.py           # スコアリング＆マッチング 【みっきー】
├── schema.sql            # DBスキーマ定義          【のずちゃん】
├── seed_data.py          # ダミー人財データ投入     【のずちゃん】
├── database.py           # SQLite CRUD操作         【のずちゃん】
│
└── data/
    └── tech0_hr.db       # SQLiteデータベース（自動生成・Git管理外）
```

---

## 開発の進め方

### ブランチ運用

`main` ブランチには直接 push しません。各自 feature ブランチで作業し、PR を出してマージします。

```bash
# 1. mainを最新にする
git checkout main
git pull origin main

# 2. 自分のブランチを作成
git checkout -b feature/自分の担当名

# 3. ファイルを修正して保存

# 4. 変更をコミット & プッシュ
git add 担当ファイル名
git commit -m "[担当名] 変更内容"
git push origin feature/自分の担当名

# 5. GitHubでプルリクエストを作成 → レビュー → mainにマージ
```

### コミットメッセージ規約

```
[担当名] 変更内容
```

例：
- `[AI API] PEST分析プロンプトに業界動向を追加`
- `[フロント] STEP5のリーンキャンバス表示レイアウト改善`
- `[DB] employeesテーブルにnew_business_scoreカラム追加`
- `[ランキング] MBTIバランス分析のロジック改善`

---

## スコアリング5軸

解決策（事業案）を以下の5軸で評価します（各1〜5点、合計25点満点）。

| 軸 | 評価観点 |
|---|---------|
| market_size | 市場規模・成長性 |
| feasibility | 実現可能性 |
| profitability | 収益性 |
| innovativeness | 革新性 |
| sustainability | 持続的優位性 |

---

## 対象企業：株式会社テクゼロン

- 東証プライム上場 / 売上高5,000億円 / 従業員12,000名
- 主力事業：産業機械製造（精密加工機、産業用ロボット、自動化ライン）
- ハードウェア売り切りからサービタイゼーション（IoT活用）への移行期
- 主要顧客：世界的な自動車・半導体・家電メーカー（海外売上比率50%超）

プロンプトにはテクゼロンの企業情報・JTC特有の制約（稟議制度、ベンダー縛り等）が組み込まれており、汎用的ではない具体的な提案が生成されます。
