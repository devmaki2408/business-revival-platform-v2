"""
crawler.py — OpenAI API 連携モジュール（外部データ取得）
========================================================
【担当者】テリー（クローラー/AI API担当）
【役割】OpenAI API を呼び出し、外部からデータを取得する。
        PEST分析・5F分析・課題生成・解決策生成・リーンキャンバス・チームマッチングを行う。

【解説】
  このファイルには2つの役割がある:
  1. プロンプト（AIへの指示文）を組み立てる関数群（ファイル後半）
  2. OpenAI API を呼び出してJSONレスポンスを返す関数群（ファイル前半）

  処理の流れ:
    プロンプト関数で指示文を作成 → _call_openai() でAPIに送信 → JSON結果を返す

【ヒント】
  - OpenAI の Python SDK: from openai import OpenAI
  - APIキーは .env ファイルに OPENAI_API_KEY=sk-xxx... と書いて管理
  - response_format={"type": "json_object"} で JSON 出力を強制
  - f-string 内で JSON の {} を書くには {{ }} とエスケープする
"""

import json
import os
from openai import OpenAI
from dotenv import load_dotenv

# .env から OPENAI_API_KEY を読み込む
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 使用するモデル（gpt-4o が高精度、gpt-4o-mini がコスト安）
MODEL = "gpt-4o"


# ============================================================
# テクゼロン社の企業コンテキスト（全プロンプト共通で使う前提情報）
# ============================================================
# 【解説】各プロンプトに会社情報を埋め込むことで、
#         AIの出力が「この会社に最適化」される。
#         JTC特有の制約（稟議、ベンダー縛り等）を入れると現実的な提案になる。

COMPANY_CONTEXT = """
## 依頼企業の前提情報（必ず考慮すること）
- 社名: 株式会社テクゼロン（東証プライム上場）
- 規模: 売上高5,000億円、従業員12,000名
- 主力事業: 産業機械製造（精密加工機、産業用ロボット、自動化ライン）
- ビジネスモデル: ハードウェア売り切りから、IoT活用のサービタイゼーション（故障予兆検知・リモートメンテナンス等）への移行期
- 主要顧客: 世界的な自動車メーカー、半導体メーカー、家電メーカー（海外売上比率50%超）
- 技術資産: 数十年分の設計図、特許、不具合対応記録、顧客カスタマイズ履歴（各部署に分散）
- 強固な顧客基盤: 現場に深く入り込んでおり、顧客の生の声（一次情報）が豊富

## JTC（日本の伝統的大企業）特有の制約
- 意思決定: 稟議制度があり、新規投資には複数階層の承認が必要
- ベンダー縛り: 既存のITベンダーとの長期契約があり、新技術導入にはベンダー選定プロセスが必要
- 品質重視文化: 「石橋を叩いて渡る」文化があり、失敗を許容しにくい
- 情報のサイロ化: 営業・設計・製造・保守のデータが統合されておらず、部署間連携に課題
- 人材: 熟練技能者の大量退職に伴う技術承継が急務
- 探索と深化: 既存事業の延長ではない「非連続な成長」を求めているが、社内アイデアが既存の枠に留まりがち

## 新規事業に期待される方向性
- 自社の技術資産（設計図、特許、不具合データ）を活用した新規事業
- 既存の顧客基盤を活かしたサービス展開
- 製造業DX・スマートファクトリー関連
- 暗黙知のデジタル化・技術承継
- 産業データプラットフォーム（ITジャイアントへの対抗）
"""


# ============================================================
# 共通ヘルパー（API呼び出し）
# ============================================================
# 【解説】すべての公開関数がこの _call_openai() を使う。
#         try-except でエラーが起きてもアプリが落ちないようにしている。
# 【ヒント】関数名の先頭に _ を付けると「このファイル内部でだけ使う」という意味になる。

def _call_openai(prompt: str, temperature: float = 0.7) -> dict:
    """
    OpenAI API を呼び出し、JSON をパースして dict で返す。
    - response_format で JSON を強制
    - パースに失敗した場合はエラー情報を返す
    """
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "あなたは優秀なビジネスコンサルタントです。必ず有効なJSON形式のみで回答してください。JSON以外の文字は一切出力しないでください。",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=temperature,
        )
        raw = response.choices[0].message.content
        return json.loads(raw)

    except json.JSONDecodeError as e:
        return {"error": f"JSONパースエラー: {e}", "raw_response": raw}
    except Exception as e:
        return {"error": f"API呼び出しエラー: {e}"}


# ============================================================
# 公開API（app.py から呼び出される関数）
# ============================================================
# 【解説】各関数は「プロンプト生成 → API呼び出し」の2ステップだけ！
#         temperature が低いほど安定した出力、高いほど創造的な出力になる。

def run_pest_analysis(market: str) -> dict:
    """PEST分析を実行する。temperature=0.5（分析系は低めで安定）"""
    prompt = _pest_prompt(market)
    return _call_openai(prompt, temperature=0.5)


def run_five_forces_analysis(market: str) -> dict:
    """5つの力分析を実行する。"""
    prompt = _five_forces_prompt(market)
    return _call_openai(prompt, temperature=0.5)


def generate_issues(market: str, existing_issues: list[str] | None = None) -> dict:
    """課題を10個生成する。temperature=0.8（創造性高め）"""
    prompt = _issues_prompt(market, existing_issues)
    return _call_openai(prompt, temperature=0.8)


def generate_solutions(
    market: str,
    issue: str,
    target: str,
    existing_solutions: list[str] | None = None,
) -> dict:
    """解決策を10個生成＆スコアリングする。"""
    prompt = _solutions_prompt(market, issue, target, existing_solutions)
    return _call_openai(prompt, temperature=0.8)


def generate_lean_canvas(
    market: str,
    issue: str,
    target: str,
    solution_title: str,
    solution_desc: str,
) -> dict:
    """リーンキャンバス（9ブロック）を生成する。"""
    prompt = _lean_canvas_prompt(market, issue, target, solution_title, solution_desc)
    return _call_openai(prompt, temperature=0.6)


def match_team(solution_text: str, employees_json: str) -> dict:
    """事業案に最適な4人チームを選抜する。temperature=0.4（堅実に）"""
    prompt = _team_matching_prompt(solution_text, employees_json)
    return _call_openai(prompt, temperature=0.4)


# ============================================================
# プロンプトテンプレート（内部用）
# ============================================================
# 【解説】各関数は「AIへの指示文（プロンプト）」を文字列で返す。
#         上の公開API関数から呼び出される。
#
# 【ヒント】
#   - f-string（f"..."）を使うと変数を埋め込める: f"市場: {market}"
#   - AIに JSON で回答させるには、出力形式を具体的に指定するのがコツ
#   - {{ }} と書くと、f-string のエスケープ（JSON の {} として出力される）


def _pest_prompt(market: str) -> str:
    """PEST分析プロンプトを生成する。"""
    return f"""あなたは優秀な経営コンサルタントで戦略コンサルタントでマーケティングコンサルタントです。
あなたは過去、顧客企業に対して数多くのコンサルティングを行い貢献をしてきました。

{COMPANY_CONTEXT}

# 依頼
上記の企業が新規参入する前提で、次の市場について PEST分析 を行い、JSON形式で出力してください。
深呼吸してstep by stepで考え、自分の限界を超えてください。

# 市場
{market}

# 出力形式（厳密にこのJSON構造で出力）
{{
  "summary": "PEST分析の要約（テクゼロンにとっての示唆を含む、100〜150文字）",
  "politics": {{
    "points": ["政治的要因1", "政治的要因2", "政治的要因3", "政治的要因4"],
    "insight": "テクゼロンが活用できる政治面の示唆"
  }},
  "economy": {{
    "points": ["経済的要因1", "経済的要因2", "経済的要因3", "経済的要因4"],
    "insight": "テクゼロンの事業規模を踏まえた経済面の示唆"
  }},
  "society": {{
    "points": ["社会的要因1", "社会的要因2", "社会的要因3", "社会的要因4"],
    "insight": "製造業の人材課題を踏まえた社会面の示唆"
  }},
  "technology": {{
    "points": ["技術的要因1", "技術的要因2", "技術的要因3", "技術的要因4"],
    "insight": "テクゼロンの技術資産を活かせる技術面の示唆"
  }}
}}

# ルール
- テクゼロンが新規参入する目的で分析してください
- テクゼロンの既存技術資産・顧客基盤をどう活かせるかの観点を含めてください
- JTCの制約（稟議・ベンダー縛り等）を考慮した現実的な分析にしてください
- 各項目4つ以上の要因を挙げてください
- 最新のトレンドやデータを考慮してください
- 具体的な企業名・法規制名を挙げてください
- JSON以外の文字は出力しないでください"""


def _five_forces_prompt(market: str) -> str:
    """5つの力分析プロンプトを生成する。"""
    return f"""あなたはマイケル・ポーター氏で、顧客セグメンテーションに特化した市場分析と競争戦略の専門家です。
あなたは過去、顧客企業に対して数多くの貢献をしてきました。

{COMPANY_CONTEXT}

# 依頼
上記の企業が新規参入する前提で、次の市場について 5つの力分析 を行い、JSON形式で出力してください。
深呼吸してstep by stepで考え、自分の限界を超えてください。

# 市場
{market}

# 出力形式（厳密にこのJSON構造で出力）
{{
  "summary": "テクゼロンにとっての5つの力分析の総評（100〜200文字）",
  "total_score": 合計点（5〜25の整数）,
  "rivalry": {{
    "points": ["競合要因1（具体的企業名を含む）", "競合要因2", "競合要因3"],
    "insight": "テクゼロンの強みを踏まえた示唆",
    "score": 1〜5の整数,
    "score_reason": "テクゼロンの立場からの点数根拠"
  }},
  "new_entrants": {{
    "points": ["新規参入の脅威1", "新規参入の脅威2", "新規参入の脅威3"],
    "insight": "示唆",
    "score": 1〜5の整数,
    "score_reason": "この点数の根拠"
  }},
  "substitutes": {{
    "points": ["代替品の脅威1", "代替品の脅威2", "代替品の脅威3"],
    "insight": "示唆",
    "score": 1〜5の整数,
    "score_reason": "この点数の根拠"
  }},
  "supplier_power": {{
    "points": ["売り手の交渉力1", "売り手の交渉力2", "売り手の交渉力3"],
    "insight": "示唆",
    "score": 1〜5の整数,
    "score_reason": "この点数の根拠"
  }},
  "buyer_power": {{
    "points": ["買い手の交渉力1", "買い手の交渉力2", "買い手の交渉力3"],
    "insight": "示唆",
    "score": 1〜5の整数,
    "score_reason": "この点数の根拠"
  }}
}}

# スコア基準
5点=参入非常に容易, 4点=参入しやすい, 3点=中程度, 2点=参入しにくい, 1点=参入非常に困難

# ルール
- テクゼロンが新規参入する目的で分析してください
- テクゼロンの既存技術・顧客基盤が参入障壁をどう下げるかも考慮してください
- 具体的な企業名やサービス名を挙げてください
- GoogleやAmazonなどITジャイアントの動向も考慮してください
- 各項目3つ以上の要因を挙げてください
- JSON以外の文字は出力しないでください"""


def _issues_prompt(market: str, existing_issues: list[str] | None = None) -> str:
    """課題生成プロンプトを生成する。"""
    # 【解説】既に生成済みの課題があれば、重複しないようプロンプトに含める
    existing_note = ""
    if existing_issues:
        items = "\n".join(f"- {issue}" for issue in existing_issues)
        existing_note = f"""
# 既出の課題（これらと似た内容は絶対に避けてください）
{items}
"""

    return f"""あなたは優秀なUXリサーチャーで人間工学と社会学の専門家です。
人々の行動や体験を深く理解するためのリサーチを行い、日常生活におけるユーザーの課題や不満を発見するのが得意です。

{COMPANY_CONTEXT}

# 依頼
上記の企業が取り組むべき観点で、次の市場に関する課題（ターゲットが抱える問題）を10個生成してください。

# 市場
{market}
{existing_note}
# 出力形式（厳密にこのJSON構造で出力）
{{
  "issues": [
    {{
      "id": 1,
      "target": "ターゲット（10文字以内、年齢層・性別・特性を含む）",
      "issue": "課題（20〜30文字以内）",
      "detail": "課題の詳細説明（テクゼロンの技術でどう解決しうるかの示唆を含む、50〜100文字）"
    }}
  ]
}}

# ルール
- ターゲットは必ずエクストリームユーザー（極端な利用者）を想定してください
- 統計学的属性・心理学的属性・行動学的属性・地理学的属性を考慮してください
- 不満/不安/不快/不信/不備の5つの「不」の観点で課題を考えてください
- テクゼロンの技術資産（精密加工、IoT、ロボット技術、産業データ）で解決しうる課題を優先
- テクゼロンの既存顧客（自動車・半導体・家電メーカー）のペインポイントも考慮
- 最新の技術やトレンドを考慮してください
- 水平思考や垂直思考、システム思考を使い分けてください
- 10個すべて異なる切り口にしてください
- JSON以外の文字は出力しないでください"""


def _solutions_prompt(market: str, issue: str, target: str,
                      existing_solutions: list[str] | None = None) -> str:
    """解決策（事業案）生成＆スコアリングプロンプトを生成する。"""
    # 【解説】既に生成済みの解決策があれば、重複しないようプロンプトに含める
    existing_note = ""
    if existing_solutions:
        items = "\n".join(f"- {s}" for s in existing_solutions)
        existing_note = f"""
# 既出の解決策（これらと似た内容は絶対に避けてください）
{items}
"""

    return f"""あなたは優秀な新規事業コンサルタントで、ベンチャーキャピタリストが即座に投資したくなる事業案を生成する専門家です。

{COMPANY_CONTEXT}

# 依頼
上記の企業の強みを活かし、次の市場・ターゲット・課題に対する解決策（事業案）を10個生成し、各案をスコアリングしてください。

# 市場
{market}

# ターゲット
{target}

# 課題
{issue}
{existing_note}
# 技術・手法（テクゼロンのリソースを活かして活用すること）
IoT, AI, 産業用ロボット, 精密加工技術, 予兆検知, デジタルツイン,
WEB3, AR/MR, ウェアラブル, シェアリング, マッチング, サブスクリプション, プラットフォーム,
既存顧客ネットワーク, 設計データ・特許資産

# 出力形式（厳密にこのJSON構造で出力）
{{
  "solutions": [
    {{
      "id": 1,
      "title": "解決策タイトル（15文字以内）",
      "description": "解決策の概要（テクゼロンの強みをどう活かすかを含む、150〜200文字）",
      "tech_used": "使用する技術・手法",
      "scoring": {{
        "market_size": {{
          "score": 1〜5の整数,
          "reason": "市場規模・成長性の根拠（30文字以内）"
        }},
        "feasibility": {{
          "score": 1〜5の整数,
          "reason": "テクゼロンのリソースを踏まえた実現可能性（30文字以内）"
        }},
        "profitability": {{
          "score": 1〜5の整数,
          "reason": "収益性の根拠（30文字以内）"
        }},
        "innovativeness": {{
          "score": 1〜5の整数,
          "reason": "革新性の根拠（30文字以内）"
        }},
        "sustainability": {{
          "score": 1〜5の整数,
          "reason": "テクゼロンの技術資産に基づく持続的優位性（30文字以内）"
        }},
        "total": 合計点（5〜25の整数）
      }}
    }}
  ]
}}

# スコアリング基準
各項目 1〜5点（5点が最高）：
- market_size（市場規模・成長性）: 市場が大きく成長余地があるか
- feasibility（実現可能性）: テクゼロンの技術・リソースで実現可能か、JTCの稟議を通せるか
- profitability（収益性）: 持続的な収益モデルを構築できるか（サブスク型が望ましい）
- innovativeness（革新性）: 既存にない新しい価値を提供できるか
- sustainability（持続的優位性）: テクゼロンの技術資産により競合が簡単に真似できない優位性があるか

# ルール
- SCAMPER法（代用・結合・適応・修正・転用・排除・再構成）を用いて新しい可能性を追求してください
- テクゼロンの既存技術・顧客基盤・データ資産を活かした事業案にしてください
- JTCの意思決定プロセス（稟議）を通しやすい現実的な事業案を心がけてください
- 解決策には必ず上記の技術・手法を1つ以上活用してください
- 10個すべて異なるアプローチにしてください
- スコアリングは厳密に根拠を持って行ってください（甘くつけない）
- total は5項目の合計値にしてください
- JSON以外の文字は出力しないでください"""


def _lean_canvas_prompt(market: str, issue: str, target: str,
                        solution_title: str, solution_desc: str) -> str:
    """リーンキャンバス（9ブロック）生成プロンプト。"""
    return f"""あなたはアッシュ・マウリャ氏で、成功するビジネスソリューションに特化したビジネス分析とプロセス最適化のビジネスアナリストの専門家です。
あなたは過去、顧客企業に対して数多くの貢献をしてきました。

{COMPANY_CONTEXT}

# 依頼
上記の企業が実行する前提で、次の事業案についてリーンキャンバスの9個のブロックを生成してください。
深呼吸してstep by stepで考え、自分の限界を超えてください。

# 市場
{market}

# ターゲット
{target}

# 課題
{issue}

# 解決策
【{solution_title}】
{solution_desc}

# 出力形式（厳密にこのJSON構造で出力）
{{
  "problem": {{
    "top3": ["課題1（最重要）", "課題2", "課題3"],
    "existing_alternatives": "既存の代替手段（顧客が現在どう対処しているか）"
  }},
  "customer_segments": {{
    "target": "ターゲット顧客（具体的に）",
    "early_adopter": "アーリーアダプター（最初に使ってくれる顧客像）"
  }},
  "unique_value_proposition": "独自の価値提案（テクゼロンだからこそ提供できる価値、50文字以内）",
  "solution": {{
    "features": ["機能1（テクゼロンの技術を活用）", "機能2", "機能3"],
    "techzeron_advantage": "テクゼロンの技術資産をどう活かすか"
  }},
  "channels": ["チャネル1（テクゼロンの既存ネットワーク活用）", "チャネル2", "チャネル3"],
  "revenue_streams": {{
    "model": "収益モデル（サブスク/従量課金/ライセンス等）",
    "pricing": "価格帯の目安",
    "ltv_estimate": "顧客生涯価値の見込み"
  }},
  "cost_structure": {{
    "fixed_costs": ["固定費1", "固定費2"],
    "variable_costs": ["変動費1", "変動費2"],
    "initial_investment": "初期投資の概算"
  }},
  "key_metrics": ["KPI1（事業の成否を測る指標）", "KPI2", "KPI3"],
  "unfair_advantage": "テクゼロンが持つ圧倒的優位性（他社が簡単にコピーできないもの）",
  "summary": "このリーンキャンバスの総評（100〜150文字）"
}}

# ルール
- テクゼロンの技術資産（精密加工技術、IoT、設計データ、特許、顧客ネットワーク）を最大限活かしてください
- JTCの制約（稟議制度、ベンダー縛り）の中でも実行可能な計画にしてください
- 収益モデルは「売り切り」ではなく「リカーリング収益（サブスク等）」を推奨
- アーリーアダプターはテクゼロンの既存顧客から特定してください
- 3年以内に黒字化できる現実的なプランにしてください
- JSON以外の文字は出力しないでください"""


def _team_matching_prompt(solution: str, employees_json: str) -> str:
    """チームマッチングプロンプトを生成する。"""
    return f"""あなたは組織開発とチームビルディングの専門家です。

{COMPANY_CONTEXT}

# 依頼
以下の事業案を実行するために最適な4人のプロジェクトチームを、社員リストから選抜してください。
テクゼロンのJTC文化（部署の壁、稟議制度）を打破できるチーム編成を意識してください。

# 事業案
{solution}

# 社員リスト（JSON）
{employees_json}

# 出力形式（厳密にこのJSON構造で出力）
{{
  "team": [
    {{
      "employee_id": 社員ID,
      "name": "氏名",
      "role": "このプロジェクトでの役割（例: PL, テックリード, マーケ担当, デザイン担当）",
      "selection_reason": "この人を選んだ理由（80〜120文字。スキル・MBTI・実績を踏まえて）",
      "strengths_for_project": "このプロジェクトで活きる強み（50文字以内）"
    }}
  ],
  "team_synergy": "4人のチームとしての相乗効果の説明（100〜150文字。MBTIの相性やスキルの補完性に言及）",
  "team_risk": "このチーム編成で想定されるリスクと対策（80〜100文字）"
}}

# 選抜基準
1. スキルマッチ: 事業案に必要なスキルセットをカバーすること
2. MBTIバランス: 外向(E)/内向(I)、思考(T)/感情(F)のバランスを考慮
3. 経験の多様性: 異なる部門・バックグラウンドから選ぶ（サイロ打破）
4. リーダーシップ: 1名はリーダーシップスコアが高い人を含める
5. 実績: 類似プロジェクトの経験者を優先
6. 0→1適性: 新規事業立ち上げに向く「探索型人材」を優先的に含める

# ルール
- 必ず4名を選んでください
- 同じ部門から2名以上選ばないでください（多様性・サイロ打破のため）
- JSON以外の文字は出力しないでください"""


# ---------- テスト用 ---------- #
if __name__ == "__main__":
    print("=== PEST分析テスト ===")
    result = run_pest_analysis("訪日外国人アニメツーリズム")
    print(json.dumps(result, ensure_ascii=False, indent=2))
