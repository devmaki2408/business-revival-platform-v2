"""
app.py — Streamlit メインアプリケーション
==========================================
【担当者】わーちゃん（フロント担当）
【役割】ユーザーインターフェースを構築する。
        「入力 → 市場分析 → 課題探索 → 解決策 → リーンキャンバス → チーム編成」
        の6ステップのフローを管理する。

【起動コマンド】streamlit run app.py

【TODO（写経ポイント）】
  1. ページ設定 & DB初期化       ★ st.set_page_config() を学ぶ
  2. セッション状態の初期化       ★ st.session_state を学ぶ
  3. サイドバー（ナビゲーション）   ★ st.sidebar と条件表示を学ぶ
  4. STEP 1: 市場・ターゲット入力  ★ st.text_input / st.button を学ぶ
  5. STEP 2: 市場分析表示         ★ st.tabs / st.expander を学ぶ
  6. STEP 3: 課題の探索           ★ 動的リスト表示とボタン連携を学ぶ
  7. STEP 4: 解決策のランキング    ★ st.columns / st.metric を学ぶ
  8. STEP 5: リーンキャンバス      ★ 新規追加！9ブロック表示を学ぶ
  9. STEP 6: チーム編成           ★ DB連携と横並び表示を学ぶ

【ヒント】
  - Streamlit は上から順に実行される（if/elif で画面を切り替える）
  - st.session_state に値を保存 → 画面遷移しても値が保持される
  - st.rerun() でページを再描画（ステップ遷移時に使う）
"""

import os
import streamlit as st
import json
from database import init_db, get_all_employees, save_session_log
from crawler import (
    run_pest_analysis,
    run_five_forces_analysis,
    generate_issues,
    generate_solutions,
    generate_lean_canvas,
)
from ranking import (
    rank_solutions,
    format_score_display,
    build_team_for_solution,
    get_mbti_compatibility_note,
    SCORING_AXES,
)

# ---------- ページ設定 ---------- #
# ★ set_page_config はスクリプトの最初に1回だけ呼ぶ

st.set_page_config(
    page_title="テクゼロン 人財駆動型・企業再興プラットフォーム",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)
# ---------- (わーちゃん追記)見た目を整える共通CSS ---------- #
# ★ ここでは「色・余白・カード感」だけをまとめて調整する。
# ★ 処理ロジックには触れず、UIの見え方だけを変えるための設定。
# ★ 後から見返したときに、どこで全体デザインを変えているか分かるように
#   app.py の上の方にまとめて置いている。

CUSTOM_CSS = """
<style>
/* ===== 全体のベース設定 ===== */
.main {
    background: linear-gradient(180deg, #050816 0%, #0b1020 100%);
}

.block-container {
    max-width: 1100px;
    padding-top: 2.6rem;
    padding-bottom: 4rem;
}

/* ===== テキストの見え方 ===== */
h1, h2, h3, h4, h5, h6 {
    color: #f8fafc;
    letter-spacing: -0.02em;
}

p, li, label, .stMarkdown, .stCaption, .stText {
    color: #d1d5db;
}

/* ===== ヒーローエリア用 ===== */
.hero-wrap {
    padding: 0.2rem 0 0.45rem 0;
}

.hero-badge {
    display: inline-block;
    padding: 0.35rem 0.85rem;
    border-radius: 999px;
    border: 1px solid rgba(129, 140, 248, 0.5);
    background: rgba(99, 102, 241, 0.12);
    color: #c4b5fd;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    margin-bottom: 0.55rem;
}

.hero-title {
    font-size: clamp(1.45rem, 3.2vw, 2.55rem);
    line-height: 1.15;
    font-weight: 850;
    color: #f8fafc;
    margin: 0 0 0.35rem 0;
    max-width: 760px;
}

.hero-title .accent {
    background: linear-gradient(90deg, #c4b5fd 0%, #8b5cf6 50%, #6366f1 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.hero-desc {
    font-size: 0.93rem;
    line-height: 1.6;
    color: #cbd5e1;
    max-width: 640px;
    margin-bottom: 0.35rem;
}

.status-badge {
    display: inline-block;
    margin-top: 0.15rem;
    padding: 0.45rem 0.8rem;
    border-radius: 999px;
    font-weight: 700;
    font-size: 0.88rem;
}

.status-badge.connected {
    background: rgba(16, 185, 129, 0.14);
    border: 1px solid rgba(16, 185, 129, 0.35);
    color: #6ee7b7;
}

.status-badge.disconnected {
    background: rgba(245, 158, 11, 0.14);
    border: 1px solid rgba(245, 158, 11, 0.35);
    color: #fcd34d;
}

/* ===== カード風の見た目 ===== */
.section-card {
    background: linear-gradient(180deg, rgba(15, 23, 42, 0.98) 0%, rgba(17, 24, 39, 0.95) 100%);
    border: 1px solid rgba(99, 102, 241, 0.30);
    border-radius: 22px;
    padding: 1rem 1.15rem;
    margin: 0.02rem 0 0.3rem 0;
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.22);
}

.section-card h3 {
    margin-top: 0;
    margin-bottom: 0.65rem;
    color: #f8fafc;
}

.section-card p {
    margin-bottom: 0.2rem;
}

.section-card.step1-card {
    border: 1px solid rgba(129, 140, 248, 0.38);
    box-shadow: 0 14px 34px rgba(79, 70, 229, 0.14);
}

.step1-card h3 {
    font-size: 1.1rem;
    margin-bottom: 0.45rem;
}

/* ===== 入力欄の見た目 ===== */
div[data-baseweb="input"] > div {
    background-color: rgba(15, 23, 42, 0.98);
    border: 1px solid rgba(129, 140, 248, 0.42);
    border-radius: 18px;
    padding: 0.95rem 0.75rem;
    box-shadow: 0 0 0 1px rgba(99, 102, 241, 0.06);
}

input {
    color: #f8fafc !important;
    font-size: 1.08rem !important;
}

/* ===== ボタンの見た目 ===== */
.stButton > button {
    border: none;
    border-radius: 16px;
    padding: 0.72rem 1.15rem;
    font-weight: 800;
    color: white;
    background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 100%);
    box-shadow: 0 10px 24px rgba(99, 102, 241, 0.28);
    transition: 0.2s ease;
}

.stButton > button:hover {
    transform: translateY(-1px);
    filter: brightness(1.05);
}

/* ===== Expander / Tabs / Metric の見た目調整 ===== */
.streamlit-expanderHeader {
    color: #f8fafc;
    font-weight: 700;
}

[data-baseweb="tab-list"] {
    gap: 0.35rem;
}

button[role="tab"] {
    border-radius: 999px !important;
    background: rgba(99, 102, 241, 0.10) !important;
    color: #cbd5e1 !important;
}

button[role="tab"][aria-selected="true"] {
    background: linear-gradient(90deg, rgba(99, 102, 241, 0.35), rgba(139, 92, 246, 0.35)) !important;
    color: #ffffff !important;
}

[data-testid="stMetric"] {
    background: rgba(15, 23, 42, 0.8);
    border: 1px solid rgba(99, 102, 241, 0.18);
    border-radius: 18px;
    padding: 0.75rem;
}

/* ===== サイドバー調整 ===== */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #050816 0%, #0b1020 100%);
    border-right: 1px solid rgba(99, 102, 241, 0.18);
}

[data-testid="stSidebar"] * {
    color: #e5e7eb;
}

/* サイドバー内のボタンもメインと寄せる */
[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    border: none;
    border-radius: 16px;
    padding: 0.72rem 1rem;
    font-weight: 800;
    color: white;
    background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 100%);
    box-shadow: 0 10px 24px rgba(99, 102, 241, 0.22);
}

[data-testid="stSidebar"] hr {
    border-color: rgba(148, 163, 184, 0.14);
}

.hero-divider {
    margin: 0.35rem 0 0.2rem 0;
    border: none;
    border-top: 1px solid rgba(148, 163, 184, 0.14);
}

/* Markdown見出しに出るアンカー風リンクアイコンを非表示 */
a.anchor-link {
    display: none !important;
}

/* ===== 区切り線を少し柔らかくする ===== */
hr {
    border-color: rgba(148, 163, 184, 0.18);
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------- OpenAI 接続状態の表示用 ---------- #
# ★ 「接続中 / 未接続」を見た目で分かるようにするための簡易フラグ。
# ★ 今回は画面上の案内用なので、環境変数の有無で判定する。
OPENAI_CONNECTED = bool(os.getenv("OPENAI_API_KEY"))

# DB 初期化
init_db()

# ---------- セッション状態の初期化 ---------- #
# ★ session_state は辞書的に使える。ページ遷移しても値が残る。

DEFAULT_STATE = {
    "current_step": 1,       # 現在のステップ (1-6)
    "market_input": "",      # 入力された市場・ターゲット
    "pest_result": None,     # PEST分析結果
    "five_forces_result": None,  # 5F分析結果
    "issues": [],            # 生成された課題一覧（累積）
    "selected_issue": None,  # 選択された課題
    "solutions": [],         # 生成された解決策一覧（累積）
    "selected_solution": None,  # 選択された解決策
    "lean_canvas_result": None,  # ★ リーンキャンバス結果
    "team_result": None,     # チーム編成結果
    "analysis_done": False,  # 市場分析完了フラグ
}

for key, default in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ---------- サイドバー ---------- #
# ★ with st.sidebar: でサイドバー内にUI要素を配置

with st.sidebar:
    st.markdown("## 🧭 ナビゲーション")

    steps = [
        "① 市場・ターゲット入力",
        "② 市場分析 (PEST/5F)",
        "③ 課題の探索",
        "④ 解決策の生成",
        "⑤ リーンキャンバス",
        "⑥ チーム編成",
    ]

    for i, step_name in enumerate(steps, start=1):
        if i < st.session_state.current_step:
            st.markdown(f"✅ ~~{step_name}~~")
        elif i == st.session_state.current_step:
            st.markdown(f"▶️ **{step_name}**")
        else:
            st.markdown(f"⬜ {step_name}")

    st.divider()

    if st.button("🔄 最初からやり直す", use_container_width=True):
        for key, default in DEFAULT_STATE.items():
            st.session_state[key] = default
        st.rerun()

    st.divider()
    st.caption("テクゼロン 人財駆動型・企業再興プラットフォーム v0.2")


# ---------- （わーちゃん変更）メインヘッダー ---------- #
# ★ st.title / st.caption に加えて
#   HTML + CSS でデザインを整えました。
# ★ ただし、見た目だけを変えていて、下の処理ロジックには影響しない。

# ★ ユーザー向け説明は短くして、「何をすればいいか」がすぐ分かる文章にする。
# ★ 接続状態は environment variable の有無で表示を出し分ける。
status_class = "connected" if OPENAI_CONNECTED else "disconnected"
status_text = "● OpenAI API 接続中" if OPENAI_CONNECTED else "● OpenAI API 未接続（デモ確認向け）"

st.markdown(
    f"""
    <div class="hero-wrap">
        <div class="hero-badge">✦ AI BUSINESS ARCHITECT</div>
        <div class="hero-title">
            テクゼロンの<strong class="accent">人財</strong>とAIで、<br>
            新規事業の仮説を設計する
        </div>
        <div class="hero-desc">
            攻めたい市場を入力すると、AIが分析と案出しを支援します。<br>
        </div>
        <div class="status-badge {status_class}">{status_text}</div>
    </div>
    <hr class="hero-divider">
    """,
    unsafe_allow_html=True,
)


# ============================================================
# STEP 1: 市場・ターゲット入力
# ============================================================
# ★ if/elif で current_step に応じて画面を切り替え

# ---わーちゃん修正(ここから)---
if st.session_state.current_step == 1:
    # ★ STEP1 は入力欄を主役にしたいので、シンプルな見出し＋補助文だけにする。
    # ★ Markdown見出しだと環境によってアンカー風アイコンが出ることがあるため、
    #   HTMLで見出しを描画して余計なリンク表示を避ける。
    st.markdown(
        """
        <div class="step1-heading">① 市場・ターゲットを入力</div>
        <div class="step1-help">分析したい市場やターゲットを入力してください。</div>
        """,
        unsafe_allow_html=True,
    )

    # ★ text_input は label が必須。
    # ★ 画面上では見せたくないので label_visibility="collapsed" で隠す。
    market = st.text_input(
        "市場・ターゲット",
        value=st.session_state.market_input,
        placeholder="例: 製造業DX×設備予兆保全、半導体製造の歩留まり改善、工場の技能承継デジタル化 ...",
        label_visibility="collapsed",
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔍 分析開始", type="primary", use_container_width=True):
            if market.strip():
                st.session_state.market_input = market.strip()
                st.session_state.current_step = 2
                st.rerun()
            else:
                st.warning("市場・ターゲットを入力してください。")

    # ★ テクゼロンの事業に合った入力例を提示。
    # ★ ここは「何を書けばいいか分からない」を防ぐための補助エリア。
    with st.expander("💡 入力例を見る（テクゼロンの強みを活かせるテーマ）"):
        st.caption("気になるテーマがあれば、そのまま押して次の分析に進めます。")
        examples = [
            "製造業DX×設備予兆保全サービス",
            "半導体製造の歩留まり改善×AI分析",
            "熟練技能者の暗黙知デジタル承継",
            "産業用ロボットのリモートメンテナンス",
            "工場のスマートファクトリー化×IoTプラットフォーム",
        ]
        for ex in examples:
            if st.button(ex, key=f"ex_{ex}"):
                st.session_state.market_input = ex
                st.session_state.current_step = 2
                st.rerun()


# ============================================================
# STEP 2: 市場分析 (PEST / 5 Forces)
# ============================================================
# ★ st.spinner でローディング表示、st.tabs でタブ切り替え

elif st.session_state.current_step == 2:
    st.header("② 市場分析")
    st.markdown(f"**対象市場:** {st.session_state.market_input}")

    # まだ分析していない場合
    if not st.session_state.analysis_done:
        with st.spinner("🔄 PEST分析と5つの力分析を実行中... (30秒ほどお待ちください)"):
            pest = run_pest_analysis(st.session_state.market_input)
            five_forces = run_five_forces_analysis(st.session_state.market_input)

            st.session_state.pest_result = pest
            st.session_state.five_forces_result = five_forces
            st.session_state.analysis_done = True
            st.rerun()

    # --- PEST分析の表示 ---
    pest = st.session_state.pest_result

    if pest and "error" not in pest:
        st.subheader("📊 PEST分析")
        st.markdown(f"**要約:** {pest.get('summary', '')}")

        pest_tabs = st.tabs(["🏛 Politics", "💰 Economy", "👥 Society", "🔬 Technology"])
        pest_keys = ["politics", "economy", "society", "technology"]
        pest_labels = ["政治的要因", "経済的要因", "社会的要因", "技術的要因"]

        for tab, key, label in zip(pest_tabs, pest_keys, pest_labels):
            with tab:
                data = pest.get(key, {})
                st.markdown(f"**{label}**")
                for point in data.get("points", []):
                    st.markdown(f"- {point}")
                st.info(f"💡 示唆: {data.get('insight', '')}")
    else:
        st.error(f"PEST分析でエラーが発生しました: {pest.get('error', '不明なエラー')}")

    st.divider()

    # --- 5F分析の表示 ---
    ff = st.session_state.five_forces_result

    if ff and "error" not in ff:
        st.subheader("⚔️ 5つの力分析")
        total = ff.get("total_score", 0)
        st.markdown(f"**総評:** {ff.get('summary', '')}")
        st.metric("参入しやすさ 合計スコア", f"{total} / 25")

        ff_keys = ["rivalry", "new_entrants", "substitutes", "supplier_power", "buyer_power"]
        ff_labels = ["業界内の競合", "新規参入の脅威", "代替品の脅威", "売り手の交渉力", "買い手の交渉力"]

        for key, label in zip(ff_keys, ff_labels):
            data = ff.get(key, {})
            score = data.get("score", 0)
            with st.expander(f"{label} — {'★' * score}{'☆' * (5-score)} ({score}/5)"):
                for point in data.get("points", []):
                    st.markdown(f"- {point}")
                st.info(f"💡 示唆: {data.get('insight', '')}")
                st.caption(f"スコア根拠: {data.get('score_reason', '')}")
    else:
        st.error(f"5F分析でエラーが発生しました: {ff.get('error', '不明なエラー')}")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ 市場を変更する"):
            st.session_state.current_step = 1
            st.session_state.analysis_done = False
            st.session_state.pest_result = None
            st.session_state.five_forces_result = None
            st.rerun()
    with col2:
        if st.button("➡️ 課題の探索へ進む", type="primary"):
            st.session_state.current_step = 3
            st.rerun()


# ============================================================
# STEP 3: 課題の探索
# ============================================================
# ★ ボタンで AI 呼び出し → 結果をリスト表示 → 選択ボタンで次へ

elif st.session_state.current_step == 3:
    st.header("③ 課題の探索")
    st.markdown(f"**対象市場:** {st.session_state.market_input}")
    st.markdown("AIがテクゼロンの技術資産を踏まえた課題を10個ずつ生成します。納得できるまで何度でも再生成できます。")

    col1, col2 = st.columns([1, 3])
    with col1:
        generate_label = "🔍 課題を生成する" if not st.session_state.issues else "🔄 さらに10個生成"
        if st.button(generate_label, type="primary", use_container_width=True):
            existing = [iss["issue"] for iss in st.session_state.issues]
            with st.spinner("🔄 課題を生成中..."):
                result = generate_issues(st.session_state.market_input, existing or None)

            if "error" not in result:
                new_issues = result.get("issues", [])
                start_id = len(st.session_state.issues) + 1
                for i, iss in enumerate(new_issues):
                    iss["id"] = start_id + i
                st.session_state.issues.extend(new_issues)
                st.rerun()
            else:
                st.error(f"エラー: {result['error']}")

    if st.session_state.issues:
        st.subheader(f"📋 課題一覧（{len(st.session_state.issues)}件）")

        for iss in st.session_state.issues:
            with st.container():
                col_a, col_b = st.columns([5, 1])
                with col_a:
                    st.markdown(
                        f"**#{iss['id']}** | 🎯 {iss.get('target', '')} | "
                        f"📌 {iss.get('issue', '')}"
                    )
                    st.caption(iss.get("detail", ""))
                with col_b:
                    if st.button("✅ 選択", key=f"sel_issue_{iss['id']}"):
                        st.session_state.selected_issue = iss
                        st.session_state.current_step = 4
                        st.rerun()
                st.divider()
    else:
        st.info("「課題を生成する」ボタンを押して、課題を生成してください。")

    if st.button("⬅️ 市場分析に戻る"):
        st.session_state.current_step = 2
        st.rerun()


# ============================================================
# STEP 4: 解決策の生成
# ============================================================
# ★ rank_solutions() でソート → st.expander + st.columns でスコア表示

elif st.session_state.current_step == 4:
    st.header("④ 解決策の生成")

    issue = st.session_state.selected_issue
    st.markdown(f"**対象市場:** {st.session_state.market_input}")
    st.markdown(f"**選択した課題:** {issue.get('issue', '')}")
    st.markdown(f"**ターゲット:** {issue.get('target', '')} — {issue.get('detail', '')}")
    st.divider()

    col1, col2 = st.columns([1, 3])
    with col1:
        gen_label = "💡 解決策を生成する" if not st.session_state.solutions else "🔄 さらに10個生成"
        if st.button(gen_label, type="primary", use_container_width=True):
            existing = [s["title"] for s in st.session_state.solutions]
            with st.spinner("🔄 テクゼロンの強みを活かした解決策を生成＆スコアリング中..."):
                result = generate_solutions(
                    st.session_state.market_input,
                    issue.get("issue", ""),
                    issue.get("target", ""),
                    existing or None,
                )

            if "error" not in result:
                new_sols = result.get("solutions", [])
                start_id = len(st.session_state.solutions) + 1
                for i, s in enumerate(new_sols):
                    s["id"] = start_id + i
                st.session_state.solutions.extend(new_sols)
                st.rerun()
            else:
                st.error(f"エラー: {result['error']}")

    if st.session_state.solutions:
        ranked = rank_solutions(st.session_state.solutions)
        st.subheader(f"🏆 解決策ランキング（{len(ranked)}件）")

        for sol in ranked:
            scoring = sol.get("scoring", {})
            total = scoring.get("total", 0)

            with st.expander(
                f"**#{sol['rank']}位** | ⭐ {total}/25 | {sol.get('title', '')} | 🛠 {sol.get('tech_used', '')}",
                expanded=(sol["rank"] <= 3),
            ):
                st.markdown(sol.get("description", ""))

                st.markdown("---")
                st.markdown("**📊 スコアリング詳細:**")

                score_cols = st.columns(5)
                for idx, (key, label) in enumerate(SCORING_AXES):
                    axis = scoring.get(key, {})
                    with score_cols[idx]:
                        s = axis.get("score", 0)
                        st.metric(label, f"{'★' * s}{'☆' * (5-s)}")
                        st.caption(axis.get("reason", ""))

                st.divider()

                if st.button("✅ この解決策でリーンキャンバスへ", key=f"sel_sol_{sol['id']}"):
                    st.session_state.selected_solution = sol
                    st.session_state.current_step = 5
                    st.rerun()
    else:
        st.info("「解決策を生成する」ボタンを押してください。")

    if st.button("⬅️ 課題選択に戻る"):
        st.session_state.current_step = 3
        st.session_state.solutions = []
        st.rerun()


# ============================================================
# STEP 5: リーンキャンバス ★ 新規追加！
# ============================================================
# ★ AIが生成した9ブロックのリーンキャンバスを表示

elif st.session_state.current_step == 5:
    st.header("⑤ リーンキャンバス")

    sol = st.session_state.selected_solution
    issue = st.session_state.selected_issue
    st.markdown(f"**選択した解決策:** {sol.get('title', '')}")
    st.markdown(f"**概要:** {sol.get('description', '')}")
    st.divider()

    # リーンキャンバスを生成
    if st.session_state.lean_canvas_result is None:
        with st.spinner("🔄 リーンキャンバスを生成中..."):
            lc = generate_lean_canvas(
                st.session_state.market_input,
                issue.get("issue", ""),
                issue.get("target", ""),
                sol.get("title", ""),
                sol.get("description", ""),
            )
            st.session_state.lean_canvas_result = lc
            st.rerun()

    lc = st.session_state.lean_canvas_result

    if lc and "error" not in lc:
        # --- リーンキャンバス 9ブロック表示 ---
        st.subheader("📋 リーンキャンバス")

        # 上段: 課題 / 解決策 / UVP / 優位性 / 顧客セグメント
        row1 = st.columns(5)

        with row1[0]:
            st.markdown("### 🔴 課題")
            prob = lc.get("problem", {})
            for p in prob.get("top3", []):
                st.markdown(f"- {p}")
            st.caption(f"既存代替手段: {prob.get('existing_alternatives', '')}")

        with row1[1]:
            st.markdown("### 💡 解決策")
            solution = lc.get("solution", {})
            for f in solution.get("features", []):
                st.markdown(f"- {f}")
            st.info(f"テクゼロンの強み活用: {solution.get('techzeron_advantage', '')}")

        with row1[2]:
            st.markdown("### ⭐ 独自の価値提案")
            st.success(lc.get("unique_value_proposition", ""))

        with row1[3]:
            st.markdown("### 🏰 圧倒的優位性")
            st.warning(lc.get("unfair_advantage", ""))

        with row1[4]:
            st.markdown("### 👥 顧客セグメント")
            cs = lc.get("customer_segments", {})
            st.markdown(f"**ターゲット:** {cs.get('target', '')}")
            st.caption(f"アーリーアダプター: {cs.get('early_adopter', '')}")

        st.divider()

        # 下段: チャネル / 収益 / コスト / KPI
        row2 = st.columns(4)

        with row2[0]:
            st.markdown("### 📢 チャネル")
            for ch in lc.get("channels", []):
                st.markdown(f"- {ch}")

        with row2[1]:
            st.markdown("### 💰 収益の流れ")
            rev = lc.get("revenue_streams", {})
            st.markdown(f"**モデル:** {rev.get('model', '')}")
            st.markdown(f"**価格帯:** {rev.get('pricing', '')}")
            st.caption(f"LTV見込: {rev.get('ltv_estimate', '')}")

        with row2[2]:
            st.markdown("### 📉 コスト構造")
            cost = lc.get("cost_structure", {})
            st.markdown("**固定費:**")
            for c in cost.get("fixed_costs", []):
                st.markdown(f"- {c}")
            st.markdown("**変動費:**")
            for c in cost.get("variable_costs", []):
                st.markdown(f"- {c}")
            st.caption(f"初期投資: {cost.get('initial_investment', '')}")

        with row2[3]:
            st.markdown("### 📊 主要指標 (KPI)")
            for kpi in lc.get("key_metrics", []):
                st.markdown(f"- {kpi}")

        st.divider()

        # 総評
        st.info(f"📝 **総評:** {lc.get('summary', '')}")

        st.divider()

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("⬅️ 解決策選択に戻る", use_container_width=True):
                st.session_state.current_step = 4
                st.session_state.lean_canvas_result = None
                st.rerun()
        with col2:
            if st.button("🔄 リーンキャンバスを再生成", use_container_width=True):
                st.session_state.lean_canvas_result = None
                st.rerun()
        with col3:
            if st.button("➡️ チーム編成へ進む", type="primary", use_container_width=True):
                st.session_state.current_step = 6
                st.rerun()
    else:
        st.error(f"リーンキャンバス生成でエラーが発生しました: {lc.get('error', '不明')}")
        if st.button("🔄 再試行"):
            st.session_state.lean_canvas_result = None
            st.rerun()


# ============================================================
# STEP 6: チーム編成
# ============================================================
# ★ build_team_for_solution() → メンバー横並び表示 → MBTI相性コメント

elif st.session_state.current_step == 6:
    st.header("⑥ 最適チーム編成")

    sol = st.session_state.selected_solution
    st.markdown(f"**選択した解決策:** {sol.get('title', '')}")
    st.markdown(f"**概要:** {sol.get('description', '')}")
    st.divider()

    # チーム編成を実行
    if st.session_state.team_result is None:
        with st.spinner("🔄 テクゼロン社員から最適な4人チームを選抜中..."):
            team_data = build_team_for_solution(
                sol.get("title", ""),
                sol.get("description", ""),
            )
            st.session_state.team_result = team_data
            st.rerun()

    team_data = st.session_state.team_result

    if team_data and "error" not in team_data:
        team = team_data.get("team", [])

        st.subheader("👥 プロジェクトチーム")

        # ★ st.columns でチームメンバーを横並び表示
        member_cols = st.columns(len(team)) if team else []

        for i, member in enumerate(team):
            with member_cols[i]:
                st.markdown(f"### 🧑‍💼 {member.get('name', '')}")
                st.markdown(f"**役割:** {member.get('role', '')}")
                st.info(f"📝 **選抜理由:**\n{member.get('selection_reason', '')}")
                st.success(f"💪 **強み:** {member.get('strengths_for_project', '')}")

                # DBから詳細情報を取得して表示
                emp_id = member.get("employee_id")
                if emp_id:
                    from database import get_employee_by_id
                    emp = get_employee_by_id(emp_id)
                    if emp:
                        st.caption(f"部門: {emp['department']} / {emp['position']}")
                        st.caption(f"MBTI: {emp['mbti']} | MBA: {'✅' if emp['has_mba'] else '—'}")
                        st.caption(f"スキル: {emp['skills']}")

        st.divider()

        # チームのシナジーとリスク
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🤝 チームシナジー")
            st.markdown(team_data.get("team_synergy", ""))

            # MBTI相性の補足情報
            team_mbtis = []
            for member in team:
                emp_id = member.get("employee_id")
                if emp_id:
                    from database import get_employee_by_id
                    emp = get_employee_by_id(emp_id)
                    if emp:
                        team_mbtis.append(emp.get("mbti", ""))
            if team_mbtis:
                st.caption(f"MBTI構成: {' / '.join(team_mbtis)}")
                st.caption(get_mbti_compatibility_note(team_mbtis))

        with col2:
            st.subheader("⚠️ 想定リスクと対策")
            st.markdown(team_data.get("team_risk", ""))

        st.divider()

        # セッション保存 & ナビゲーション
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("💾 この結果を保存", use_container_width=True):
                log_id = save_session_log(
                    market_input=st.session_state.market_input,
                    pest_result=st.session_state.pest_result,
                    five_forces_result=st.session_state.five_forces_result,
                    selected_issue=json.dumps(st.session_state.selected_issue, ensure_ascii=False),
                    selected_solution=json.dumps(st.session_state.selected_solution, ensure_ascii=False),
                    lean_canvas_result=st.session_state.lean_canvas_result,
                    team_members=team_data,
                )
                st.success(f"✅ セッションを保存しました (ID: {log_id})")

        with col2:
            if st.button("🔄 別のチーム編成を試す", use_container_width=True):
                st.session_state.team_result = None
                st.rerun()

        with col3:
            if st.button("⬅️ リーンキャンバスに戻る", use_container_width=True):
                st.session_state.current_step = 5
                st.session_state.team_result = None
                st.rerun()
    else:
        st.error(f"チーム編成でエラーが発生しました: {team_data.get('error', '不明')}")
        if st.button("🔄 再試行"):
            st.session_state.team_result = None
            st.rerun()
