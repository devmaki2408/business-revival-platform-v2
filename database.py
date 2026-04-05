"""
database.py — SQLite データベース操作モジュール
================================================
【担当者】のずちゃん（DB担当）
【役割】SQLiteへの接続管理、社員データの取得、セッションログの保存を行う。
        ダミー人財データの定義と投入もこのファイルで管理する。
        他のモジュール（app.py, ranking.py）から呼び出される「データの窓口」。

【解説】
  このファイルの構成:
  1. DB接続の管理（get_connection）
  2. テーブル初期化（init_db） — schema.sql を読み込んでテーブルを作る
  3. ダミー社員データの定義と投入（EMPLOYEES, seed）
  4. 社員データの取得（SELECT系の関数）
  5. セッションログの保存（INSERT系の関数）

【ヒント】
  - sqlite3 は Python 標準ライブラリ（pip install 不要）
  - conn.row_factory = sqlite3.Row で結果を dict 風に扱える
  - SQL の ? はプレースホルダー（SQLインジェクション対策として必須）
"""

import json
import csv
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path("data/tech0_hr.db")


# ============================================================
# ダミー社員データ（テクゼロン社20名分）
# ============================================================
# 【解説】テクゼロンは産業機械メーカーなので、部門名を
#         「技術開発部」「製造部」「設計部」等にしている。
#         MBTI は16タイプからバランスよく配置（チーム編成結果に影響する）。
#         スコアは 1.0〜5.0 の範囲で、現実的にばらつきを持たせている。
#
# 各タプルの順番:
#   (name, age, gender, department, position, years_exp,
#    skills, mbti, has_mba, past_projects, specialty,
#    leadership, creativity, execution, communication, profile_summary)

EMPLOYEES = [
    ("田中 太郎", 48, "男性", "経営企画部", "部長",
     22, "経営戦略,M&A,財務分析,プロジェクト管理,中期経営計画", "ENTJ", 1,
     "新規事業立ち上げ(IoTサービス),海外拠点設立,中期経営計画策定", "経営戦略・事業開発",
     4.8, 3.5, 4.5, 4.2, "大手コンサルから転職。産業機械業界の新規事業立ち上げ経験豊富"),

    ("鈴木 花子", 38, "女性", "マーケティング部", "課長",
     15, "デジタルマーケティング,データ分析,ブランディング,BtoB営業支援,展示会企画", "ENFJ", 1,
     "製造業向けDXブランディング,リブランディングPJ,CRM導入", "BtoBマーケティング戦略",
     4.0, 4.5, 4.0, 4.8, "MBA取得後マーケ一筋。製造業のBtoBマーケティング変革を推進"),

    ("佐藤 健一", 35, "男性", "技術開発部", "主任",
     10, "Python,機械学習,AWS,Docker,FastAPI,予兆検知,デジタルツイン", "INTP", 0,
     "故障予兆検知システム開発,社内DX推進,IoTプラットフォーム構築", "AI・機械学習・IoT",
     2.5, 4.8, 4.2, 3.0, "博士号持ちのAIエンジニア。製造現場のデータ分析に強み"),

    ("高橋 美咲", 29, "女性", "デザイン部", "デザイナー",
     6, "UI/UX設計,Figma,ユーザーリサーチ,産業用HMI設計,Design Thinking", "INFP", 0,
     "操作パネルUI刷新,リモートメンテナンスアプリUX改善,社内ツールUX改善", "産業用UXデザイン",
     2.8, 4.9, 3.5, 4.0, "工業デザイン出身。産業機械のヒューマンインターフェース設計が強み"),

    ("伊藤 大輝", 45, "男性", "営業部", "部長",
     20, "法人営業,交渉術,パートナーシップ構築,グローバル営業,自動車業界知識", "ESTP", 0,
     "大手自動車メーカーアライアンス締結,海外販路開拓,サービス契約拡大", "グローバル法人営業",
     4.5, 3.0, 4.8, 4.5, "自動車業界の人脈が広い。海外顧客との交渉に長けたトップセールス"),

    ("渡辺 理恵", 36, "女性", "人事部", "課長",
     13, "組織開発,採用戦略,人材育成,タレントマネジメント,コーチング", "ESFJ", 1,
     "人事制度改革,技能承継プログラム設計,リーダー育成,ジョブ型導入検討", "組織開発・人材育成",
     4.2, 3.8, 3.8, 4.9, "テクゼロンの人材改革の中心人物。技能承継のデジタル化を推進中"),

    ("中村 翔太", 30, "男性", "IT基盤部", "エンジニア",
     7, "React,TypeScript,Node.js,Azure,クラウドアーキテクチャ,Agile開発", "ISTP", 0,
     "社内ポータル開発,顧客向けリモート監視Webアプリ開発,API基盤構築", "フルスタック開発",
     2.0, 4.2, 4.5, 3.2, "スタートアップから転職。テクゼロンのクラウド移行を推進中"),

    ("山本 あかり", 42, "女性", "経理財務部", "課長",
     18, "財務分析,管理会計,資金調達,投資評価,サブスク収益モデル設計", "ISTJ", 1,
     "IoTサービス収益モデル構築,原価管理システム導入,投資評価モデル構築", "財務・管理会計",
     3.5, 2.8, 4.8, 3.5, "数字に強い財務のプロ。サブスクリプション型収益モデルの設計経験あり"),

    ("小林 拓也", 39, "男性", "新規事業開発室", "室長",
     16, "ビジネスモデル設計,リーンスタートアップ,MVP開発,VC交渉,ピッチ,産学連携", "ENTP", 1,
     "社内ベンチャー3件立ち上げ,CVC投資先選定,アクセラレーター運営", "新規事業・イノベーション",
     4.3, 4.7, 4.0, 4.5, "テクゼロンの社内起業家第1号。失敗を恐れず仮説検証を高速で回す"),

    ("加藤 さくら", 33, "女性", "法務部", "主任",
     9, "契約法務,知的財産,コンプライアンス,個人情報保護,技術ライセンス", "INTJ", 0,
     "新規事業法務レビュー,特許出願支援,GDPR対応,データ利活用規約策定", "法務・知財戦略",
     3.0, 3.2, 4.5, 3.8, "テクゼロンの特許戦略を担当。データビジネスの法務知識に強み"),

    ("松本 慎吾", 52, "男性", "製造部", "部長",
     28, "生産管理,品質管理,サプライチェーン,リーン製造,IoT,工場自動化", "ESTJ", 0,
     "工場IoT化推進,品質改善プロジェクト,海外工場立ち上げ3拠点", "製造・サプライチェーン",
     4.5, 2.5, 4.9, 3.8, "製造現場を知り尽くしたベテラン。実行力と現場改善力が抜群"),

    ("吉田 ひなた", 27, "女性", "マーケティング部", "担当",
     4, "デジタルマーケ,コンテンツ制作,動画編集,展示会運営,LinkedIn運用", "ENFP", 0,
     "海外展示会出展企画,技術ブログ立ち上げ,SNSフォロワー拡大施策", "デジタルコンテンツマーケ",
     2.2, 4.8, 3.5, 4.5, "Z世代のBtoBマーケター。製造業のデジタルプレゼンスを強化中"),

    ("井上 誠", 46, "男性", "IT基盤部", "課長",
     22, "クラウドアーキテクチャ,セキュリティ,SAP,ネットワーク,PM,OTセキュリティ", "ISTJ", 0,
     "基幹システム刷新,クラウド移行PJ,工場ネットワークセキュリティ強化", "IT/OT基盤・セキュリティ",
     3.8, 2.5, 4.5, 3.5, "IT基盤の安定稼働を支えるプロ。OT/ITの融合に取り組む"),

    ("木村 遥", 34, "女性", "経営企画部", "主任",
     10, "事業計画策定,市場調査,競合分析,統計分析,産業レポート分析", "INFJ", 0,
     "中期経営計画策定,新規市場参入調査,M&Aデューデリジェンス", "事業企画・市場分析",
     3.2, 4.0, 3.8, 4.2, "分析力と洞察力で事業の方向性を見定めるストラテジスト"),

    ("山田 龍之介", 40, "男性", "営業部", "課長",
     16, "ソリューション営業,CRM,Salesforce,顧客分析,サービス提案,半導体業界知識", "ESFP", 0,
     "半導体メーカー向けサービス契約拡大,大手顧客深耕,営業DX推進", "ソリューション営業",
     3.8, 3.2, 4.2, 4.8, "半導体業界に精通。顧客の課題を深く理解しサービス化提案を推進"),

    ("藤田 優子", 31, "女性", "技術開発部", "エンジニア",
     7, "データ分析,SQL,Tableau,Python,統計学,時系列分析,振動解析", "INTP", 0,
     "設備稼働データ分析PJ,KPIダッシュボード構築,予兆検知モデル開発", "データ分析・設備診断",
     2.5, 4.0, 4.0, 3.5, "製造データの解析が得意。設備診断の知見を持つデータサイエンティスト"),

    ("石川 大地", 50, "男性", "総務部", "部長",
     25, "総務管理,BCP策定,施設管理,IR,サステナビリティ推進", "ISFJ", 0,
     "本社移転PJ,BCP策定・訓練,統合報告書作成,ESG評価向上施策", "総務・IR・サステナビリティ",
     4.0, 2.2, 4.2, 4.0, "テクゼロンの屋台骨を支える。サステナビリティ経営の推進役"),

    ("中島 瑠奈", 28, "女性", "デザイン部", "デザイナー",
     4, "3Dモデリング,CAD,工業デザイン,Illustrator,プロトタイピング,AR可視化", "ISFP", 0,
     "次世代加工機デザインPJ,AR保守マニュアル開発,展示会ブースデザイン", "工業デザイン・AR",
     1.8, 4.9, 3.2, 3.5, "工業デザインとAR可視化のスキルを持つ若手。プロトタイピングが速い"),

    ("三浦 和也", 41, "男性", "研究開発部", "主任研究員",
     17, "材料科学,精密加工技術,特許分析,実験設計,論文執筆,産学連携", "INTJ", 1,
     "次世代加工技術開発,大学との共同研究,特許取得25件,ナノレベル加工実証", "R&D・精密加工技術",
     3.0, 4.5, 3.8, 2.8, "テクゼロンの技術の要。精密加工技術の権威で特許戦略にも精通"),

    ("岡田 真由", 37, "女性", "カスタマーサクセス部", "リーダー",
     12, "カスタマーサクセス,CX設計,リモートメンテナンス,NPS改善,Zendesk", "ENFJ", 0,
     "CS部門立ち上げ,NPS20pt改善達成,リモート保守サービス企画,サービタイゼーション推進", "カスタマーサクセス・サービタイゼーション",
     3.8, 3.8, 4.0, 4.9, "テクゼロンのサービタイゼーション推進の中心人物。顧客の声を事業に繋げる"),
]


# ============================================================
# 接続管理
# ============================================================
# 【解説】row_factory を設定すると row["name"] のように辞書風にアクセスできて便利！

def get_connection() -> sqlite3.Connection:
    """SQLite データベースへの接続を返す。"""
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================
# テーブル初期化 & データ投入
# ============================================================

def init_db():
    """
    schema.sql を実行してテーブルを初期化する。
    社員データが0件なら自動でダミーデータを投入する（初回起動時のみ）。
    """
    conn = get_connection()
    with open("schema.sql", "r", encoding="utf-8") as f:
        conn.executescript(f.read())

    # 社員データが空なら自動投入
    cursor = conn.execute("SELECT COUNT(*) FROM employees")
    count = cursor.fetchone()[0]
    conn.close()

    # 起動時に引数あり（python app.py seed）の場合は、Trueとする
    is_seed = "seed" in sys.argv

    if count == 0 or is_seed:
        seed()


def seed():
    """
    ダミーデータを DB に投入する。
    【解説】executemany() でも可能だが、ここでは1件ずつ INSERT している。
            ? はプレースホルダーで、SQLインジェクション対策として必須。
    """
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))

    # schema.sql を読み込んでテーブル作成
    with open("schema.sql", "r", encoding="utf-8") as f:
        conn.executescript(f.read())

    # 既存データを削除して再投入
    cursor = conn.cursor()
    cursor.execute("DELETE FROM employees")

    #CSVファイルの従業員データの読み込み
    csv_file ="employees.csv"

    with open(csv_file, "r", encoding="utf-8") as f:        
        reader = csv.reader(f)
        next(reader) 
        employyes_data = list(reader)

    # Bulk Insertに変更
    cursor.executemany("""
            INSERT INTO employees
                (name, age, gender, department, position, years_experience,
                 skills, mbti, has_mba, past_projects, specialty,
                 leadership_score, creativity_score, execution_score,
                 communication_score, profile_summary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, employyes_data)

    conn.commit()
    print(f"{len(employyes_data)}名のテクゼロン人財データを登録しました")
    conn.close()


# ============================================================
# 社員データ取得
# ============================================================

def get_all_employees() -> list[dict]:
    """
    全社員データを取得して dict のリストで返す。
    【ヒント】[dict(row) for row in rows] で sqlite3.Row → dict に変換
    """
    conn = get_connection()
    cursor = conn.execute("SELECT * FROM employees ORDER BY id")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_employee_by_id(employee_id: int) -> dict | None:
    """
    社員IDで1名分のデータを取得する。
    【ヒント】パラメータは (employee_id,) とタプルで渡す（カンマ忘れに注意！）
    """
    conn = get_connection()
    cursor = conn.execute("SELECT * FROM employees WHERE id = ?", (employee_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_employees_by_ids(ids: list[int]) -> list[dict]:
    """
    複数の社員IDでデータを取得する。
    【ヒント】IN句の ? を動的に生成する: ",".join("?" * len(ids))
    """
    if not ids:
        return []
    placeholders = ",".join("?" * len(ids))
    conn = get_connection()
    cursor = conn.execute(
        f"SELECT * FROM employees WHERE id IN ({placeholders})", ids
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def search_employees_by_skill(skill: str) -> list[dict]:
    """
    スキルで社員を部分一致検索する。
    【ヒント】LIKE '%Python%' のように前後に % をつけて部分一致
    """
    conn = get_connection()
    cursor = conn.execute(
        "SELECT * FROM employees WHERE skills LIKE ?", (f"%{skill}%",)
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


# ============================================================
# セッションログ
# ============================================================

def save_session_log(
    market_input: str,
    pest_result: dict | None = None,
    five_forces_result: dict | None = None,
    selected_issue: str | None = None,
    selected_solution: str | None = None,
    lean_canvas_result: dict | None = None,
    team_members: list | None = None,
) -> int:
    """
    1回のセッション結果をログとして保存する。
    【ヒント】dict/list は json.dumps() で文字列に変換してから保存する。

    Returns:
        int: 挿入されたログのID
    """
    conn = get_connection()
    cursor = conn.execute(
        """
        INSERT INTO session_logs
            (market_input, pest_result, five_forces_result,
             selected_issue, selected_solution, lean_canvas_result, team_members)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            market_input,
            json.dumps(pest_result, ensure_ascii=False) if pest_result else None,
            json.dumps(five_forces_result, ensure_ascii=False) if five_forces_result else None,
            selected_issue,
            selected_solution,
            json.dumps(lean_canvas_result, ensure_ascii=False) if lean_canvas_result else None,
            json.dumps(team_members, ensure_ascii=False) if team_members else None,
        ),
    )
    conn.commit()
    log_id = cursor.lastrowid
    conn.close()
    return log_id


# ---------- テスト用 ---------- #
if __name__ == "__main__":
    # 単体で実行するとダミーデータを投入して確認できる
    seed()
    employees = get_all_employees()
    print(f"テクゼロン社員数: {len(employees)}")
    for emp in employees[:3]:
        print(f"  {emp['name']} ({emp['department']}) - MBTI: {emp['mbti']}")
