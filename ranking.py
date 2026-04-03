"""
ranking.py — 人財マッチング & スコアリング ロジック
=====================================================
【担当者】みっきー（ランキング担当）
【役割】解決策のスコアリング表示ロジックと、テクゼロン社員DBからの最適チーム選抜を行う。

【解説】
  このファイルの構成:
  1. SCORING_AXES  — スコアリング5軸の定義（app.py からも参照される）
  2. rank_solutions()  — 解決策をスコア順にソートする
  3. format_score_display()  — スコアを星表示に変換する
  4. build_team_for_solution()  — DB → AI → チーム編成結果を返す
  5. MBTI相性ヘルパー  — チームのMBTIバランスを分析する

  このモジュールは crawler.py と database.py の両方を使う「橋渡し役」。

【ヒント】
  - ランキングは sorted() + lambda で簡単に実装できる
  - チーム編成は DB → AI に渡す → 結果を返す の3ステップ
"""

import json
from database import get_all_employees
from crawler import match_team


# ============================================================
# 解決策のスコアリング・ランキング
# ============================================================

# スコアリング5軸の定義（app.py からも参照される定数）
SCORING_AXES = [
    ("market_size", "市場規模/成長性"),
    ("feasibility", "実現可能性"),
    ("profitability", "収益性"),
    ("innovativeness", "革新性"),
    ("sustainability", "持続的優位性"),
]


def rank_solutions(solutions: list[dict]) -> list[dict]:
    """
    解決策をスコアの合計値で降順ソートする。

    【解説】
      sorted() の key に lambda を使うと、何を基準にソートするかを指定できる。
      reverse=True で降順（大きい順）にする。
      その後 enumerate() で 1位, 2位... と順位番号を振る。
    """
    # total でソート（高い順）
    sorted_solutions = sorted(
        solutions,
        key=lambda s: s.get("scoring", {}).get("total", 0),
        reverse=True,
    )

    # ランキング番号を付与
    for i, sol in enumerate(sorted_solutions, start=1):
        sol["rank"] = i

    return sorted_solutions


def format_score_display(scoring: dict) -> str:
    """
    スコアリング結果を見やすい文字列に変換する。

    【解説】
      "★" * score で星を繰り返し表示できる。
      例: score=4 → "★★★★☆"
    """
    lines = []
    for key, label in SCORING_AXES:
        axis = scoring.get(key, {})
        score = axis.get("score", 0)
        reason = axis.get("reason", "")
        bar = "★" * score + "☆" * (5 - score)
        lines.append(f"{label}: {bar} ({score}/5) - {reason}")

    total = scoring.get("total", 0)
    lines.append(f"──────────────────")
    lines.append(f"総合スコア: {total} /  25")
    return "\n".join(lines)


# ============================================================
# チームマッチング
# ============================================================

def build_team_for_solution(solution_title: str, solution_desc: str) -> dict:
    """
    選択された解決策に最適な4人チームを編成する。

    【解説】処理の流れ:
      1. DB から全社員を取得
      2. AI に渡す用の社員情報（必要フィールドのみ）に整形
      3. crawler.match_team に社員リスト+解決策を渡す
      4. AIの選抜結果を返す
    """
    # 全社員データ取得
    employees = get_all_employees()

    # AI に渡す用の社員情報（必要フィールドのみ抜粋）
    emp_for_ai = []
    for emp in employees:
        emp_for_ai.append({
            "id": emp["id"],
            "name": emp["name"],
            "age": emp["age"],
            "department": emp["department"],
            "position": emp["position"],
            "years_experience": emp["years_experience"],
            "skills": emp["skills"],
            "mbti": emp["mbti"],
            "has_mba": emp["has_mba"],
            "past_projects": emp["past_projects"],
            "specialty": emp["specialty"],
            "leadership_score": emp["leadership_score"],
            "creativity_score": emp["creativity_score"],
            "execution_score": emp["execution_score"],
            "communication_score": emp["communication_score"],
            "profile_summary": emp["profile_summary"],
        })

    # JSON文字列に変換（ensure_ascii=False で日本語をそのまま出力）
    employees_json = json.dumps(emp_for_ai, ensure_ascii=False)
    solution_text = f"【{solution_title}】\n{solution_desc}"

    result = match_team(solution_text, employees_json)
    return result


# ============================================================
# MBTI 相性ヘルパー
# ============================================================

# MBTIの相性テーブル（対極タイプが補完関係）
MBTI_COMPLEMENTS = {
    "ENTJ": ["INTP", "INFP", "ISTP"],
    "ENTP": ["INTJ", "INFJ", "ISTJ"],
    "ENFJ": ["INFP", "ISTP", "INTP"],
    "ENFP": ["INTJ", "ISTJ", "INFJ"],
    "INTJ": ["ENTP", "ENFP", "ESTP"],
    "INTP": ["ENTJ", "ENFJ", "ESTJ"],
    "INFJ": ["ENTP", "ENFP", "ESTP"],
    "INFP": ["ENTJ", "ENFJ", "ESTJ"],
    "ESTJ": ["INTP", "INFP", "ISTP"],
    "ESTP": ["INTJ", "INFJ", "ISTJ"],
    "ESFJ": ["ISTP", "INTP", "INFP"],
    "ESFP": ["ISTJ", "INTJ", "INFJ"],
    "ISTJ": ["ENTP", "ENFP", "ESTP"],
    "ISTP": ["ENTJ", "ENFJ", "ESFJ"],
    "ISFJ": ["ENTP", "ESTP", "ENFP"],
    "ISFP": ["ENTJ", "ESTJ", "ENFJ"],
}


def get_mbti_compatibility_note(team_mbtis: list[str]) -> str:
    """
    チームの MBTI 構成からバランスコメントを返す。

    【解説】
      sum(1 for m in team_mbtis if 条件) で条件に合う数をカウントしている。
      MBTIの1文字目が E=外向型、I=内向型。
      MBTIの3文字目が T=思考型、F=感情型。
    """
    e_count = sum(1 for m in team_mbtis if m and m[0] == "E")
    i_count = sum(1 for m in team_mbtis if m and m[0] == "I")
    t_count = sum(1 for m in team_mbtis if m and len(m) >= 3 and m[2] == "T")
    f_count = sum(1 for m in team_mbtis if m and len(m) >= 3 and m[2] == "F")

    notes = []
    if e_count >= 3:
        notes.append("外向型が多くアクティブな議論が期待できるが、内省の時間も意識的に確保すべき")
    elif i_count >= 3:
        notes.append("内向型が多く深い思考が期待できるが、外部発信やプレゼンの役割分担に注意")
    else:
        notes.append("外向/内向のバランスが良い")

    if t_count >= 3:
        notes.append("論理・分析重視のチーム。感情面やユーザー共感の視点を補強する工夫が必要")
    elif f_count >= 3:
        notes.append("共感・調和重視のチーム。定量分析やロジカルな意思決定を意識すべき")
    else:
        notes.append("思考/感情のバランスが良い")

    return "。".join(notes) + "。"


# ---------- テスト用 ---------- #
if __name__ == "__main__":
    dummy = [
        {"id": 1, "title": "案A", "scoring": {"total": 18}},
        {"id": 2, "title": "案B", "scoring": {"total": 22}},
        {"id": 3, "title": "案C", "scoring": {"total": 15}},
    ]
    ranked = rank_solutions(dummy)
    for s in ranked:
        print(f"Rank {s['rank']}: {s['title']} (スコア: {s['scoring']['total']})")
