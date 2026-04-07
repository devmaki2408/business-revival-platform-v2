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
from PIL import Image
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
    page_title="テクゼロン 新規事業設計支援アプリ",
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

.page-step-title {
    font-size: 1.45rem;
    line-height: 1.25;
    font-weight: 800;
    color: #f8fafc;
    margin: 0.1rem 0 0.9rem 0;
}

.step1-help {
    margin: 0 0 0.95rem 0;
}

p, li, label, .stMarkdown, .stCaption, .stText {
    color: #d1d5db;
    font-size: 1.12rem;
    line-height: 1.85;
}

.issue-card {
    padding: 0.7rem 0.9rem 0.75rem 0.9rem;
    border-radius: 16px;
    border: 1px solid transparent;
    transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease, background 0.18s ease;
    cursor: pointer;
}

.issue-card:hover {
    transform: translateY(-2px);
    background: rgba(99, 102, 241, 0.04);
    border: 1px solid rgba(129, 140, 248, 0.18);
    box-shadow: 0 8px 22px rgba(99, 102, 241, 0.06);
}

.issue-card.selected {
    padding: 0.7rem 0.9rem 0.75rem 0.9rem;
    background: rgba(99, 102, 241, 0.10);
    border: 1px solid rgba(129, 140, 248, 0.34);
    box-shadow: 0 10px 24px rgba(99, 102, 241, 0.10);
}

.issue-selected-note {
    display: inline-block;
    margin-top: 0.55rem;
    padding: 0.32rem 0.62rem;
    border-radius: 999px;
    background: rgba(99, 102, 241, 0.14);
    border: 1px solid rgba(129, 140, 248, 0.28);
    color: #c4b5fd;
    font-size: 0.92rem;
    font-weight: 700;
}

.issue-title {
    font-size: 1.22rem;
    line-height: 1.7;
    color: #f8fafc;
    font-weight: 800;
    margin-bottom: 0.2rem;
}

.issue-number {
    display: inline-block;
    min-width: 2.4rem;
    color: #a5b4fc;
    font-weight: 800;
    margin-right: 0.35rem;
}

.issue-persona {
    font-size: 1.08rem;
    line-height: 1.7;
    color: #cbd5e1;
    margin-bottom: 0.3rem;
}

.issue-detail {
    font-size: 1.1rem;
    line-height: 1.8;
    color: #cbd5e1;
}

/* StreamlitのMarkdown本文・箇条書きも少し大きめに統一 */
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {
    font-size: 1.12rem !important;
    line-height: 1.85 !important;
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
    font-size: clamp(1.55rem, 3.4vw, 2.7rem);
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
    font-size: 1.12rem;
    line-height: 1.85;
    color: #cbd5e1;
    max-width: 760px;
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

.analysis-loading-header {
    display: flex;
    align-items: center;
    gap: 0.72rem;
    margin-bottom: 0.35rem;
}

.analysis-loading-spinner {
    width: 18px;
    height: 18px;
    border: 2.5px solid rgba(191, 219, 254, 0.22);
    border-top-color: #93c5fd;
    border-radius: 999px;
    animation: analysisSpin 0.9s linear infinite;
    flex-shrink: 0;
}

@keyframes analysisSpin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

.analysis-loading-title {
    font-size: 1.18rem;
    font-weight: 800;
    color: #bfdbfe;
    margin: 0;
}

.analysis-loading-body {
    font-size: 1.08rem;
    line-height: 1.8;
    color: #e0f2fe;
}

.team-loading-card {
    position: fixed;
    left: calc(50% + 135px);
    bottom: 10.2rem;
    transform: translateX(-50%);
    width: min(920px, calc(100vw - 20rem));
    max-width: 920px;
    z-index: 9999;
    background: linear-gradient(180deg, rgba(29, 38, 67, 0.98) 0%, rgba(17, 24, 39, 0.96) 100%);
    border: 1px solid rgba(96, 165, 250, 0.32);
    border-radius: 20px;
    padding: 1rem 1.1rem;
    margin: 0;
    box-shadow: 0 12px 28px rgba(59, 130, 246, 0.18);
}

@media (max-width: 1100px) {
    .team-loading-card {
        left: 50%;
        width: calc(100vw - 3rem);
        max-width: none;
    }
}

.team-loading-header {
    display: flex;
    align-items: center;
    gap: 0.72rem;
    margin-bottom: 0.35rem;
}

.team-loading-spinner {
    width: 18px;
    height: 18px;
    border: 2.5px solid rgba(191, 219, 254, 0.22);
    border-top-color: #93c5fd;
    border-radius: 999px;
    animation: analysisSpin 0.9s linear infinite;
    flex-shrink: 0;
}

.team-loading-title {
    font-size: 1.18rem;
    font-weight: 800;
    color: #bfdbfe;
    margin: 0;
}

.team-loading-body {
    font-size: 1.08rem;
    line-height: 1.8;
    color: #e0f2fe;
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
    font-size: 1.12rem;
    line-height: 1.85;
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
[data-testid="stTextInput"] {
    margin-bottom: 0.38rem;
}
/* STEP1の主ボタンだけを少し上に寄せる */
.step1-primary-button {
    margin-top: -1.5rem;
    margin-bottom: 0.35rem;
}

[data-testid="stTextInput"] [data-baseweb="input"] {
    background-color: rgba(15, 23, 42, 0.98);
    border: 1px solid rgba(129, 140, 248, 0.42);
    border-radius: 18px;
    min-height: 56px;
    box-shadow: 0 0 0 1px rgba(99, 102, 241, 0.06);
    box-sizing: border-box;
    overflow: hidden;
}

[data-testid="stTextInput"] [data-baseweb="input"] > div {
    min-height: 56px;
    padding: 0 0.9rem;
    display: flex;
    align-items: center;
    box-sizing: border-box;
}

[data-testid="stTextInput"] input {
    color: #f8fafc !important;
    font-size: 1.15rem !important;
    line-height: 1.35 !important;
    height: auto !important;
    min-height: 1.4rem !important;
    padding: 0 !important;
    margin: 0 !important;
    background: transparent !important;
}

/* ===== ボタンの見た目 ===== */
/* ★ UX上、すべてのボタンが同じ見た目だと「戻る」と「進む」が判別しづらい。
   そのため、デフォルトボタン（戻る・補助操作）は落ち着いた見た目、
   type="primary" のボタン（生成・次へ進む）は強調表示に分ける。 */

/* デフォルトボタン = 補助操作（追加生成など） */
.stButton > button {
    border: 1px solid rgba(129, 140, 248, 0.48);
    border-radius: 16px;
    padding: 0.9rem 1.15rem;
    min-height: 62px;
    font-weight: 800;
    color: #ede9fe;
    background: rgba(30, 41, 59, 0.96);
    box-shadow: 0 6px 16px rgba(99, 102, 241, 0.08);
    transition: 0.2s ease;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    line-height: 1.35;
}

.stButton > button:hover {
    transform: translateY(-1px);
    background: rgba(51, 65, 85, 0.98);
    border-color: rgba(129, 140, 248, 0.68);
}

/* tertiary = 戻るなど、さらに控えめなボタン */
.stButton > button[kind="tertiary"] {
    border: 1px solid rgba(148, 163, 184, 0.18);
    color: #cbd5e1;
    background: rgba(15, 23, 42, 0.70);
    box-shadow: none;
}

.stButton > button[kind="tertiary"]:hover {
    background: rgba(30, 41, 59, 0.82);
    border-color: rgba(148, 163, 184, 0.28);
}

/* 主要ボタン = 生成 / 分析開始 / 次へ進む */
.stButton > button[kind="primary"] {
    border: none;
    color: white;
    background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 100%);
    box-shadow: 0 10px 24px rgba(99, 102, 241, 0.28);
}

.stButton > button[kind="primary"]:hover {
    filter: brightness(1.05);
}

/* ===== Expander / Tabs / Metric の見た目調整 ===== */
.streamlit-expanderHeader {
    color: #f8fafc;
    font-weight: 800;
    font-size: 1.12rem;
    line-height: 1.55;
}

/* Streamlit実DOM向け: expanderの見出し行そのものを強調 */
[data-testid="stExpander"] details {
    border: 1px solid rgba(99, 102, 241, 0.22);
    border-radius: 14px;
    background: rgba(15, 23, 42, 0.76);
    overflow: hidden;
}

[data-testid="stExpander"] details summary {
    padding: 0.72rem 0.9rem;
    background: linear-gradient(180deg, rgba(30, 41, 59, 0.92) 0%, rgba(17, 24, 39, 0.92) 100%);
    border-bottom: 1px solid rgba(99, 102, 241, 0.14);
}

[data-testid="stExpander"] details summary:hover {
    background: linear-gradient(180deg, rgba(51, 65, 85, 0.98) 0%, rgba(30, 41, 59, 0.96) 100%);
}

[data-testid="stExpander"] details summary p {
    color: #f8fafc !important;
    font-size: 1.18rem !important;
    font-weight: 800 !important;
    line-height: 1.55 !important;
    margin: 0 !important;
}

[data-testid="stExpander"] details summary svg {
    width: 1rem;
    height: 1rem;
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
.sidebar-logo-card {
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.08) 0%, rgba(148, 163, 184, 0.06) 100%);
    border: 1px solid rgba(148, 163, 184, 0.18);
    border-radius: 16px;
    padding: 0.65rem 0.7rem;
    margin: 0.1rem 0 0.85rem 0;
    text-align: center;
}

.sidebar-logo-card [data-testid="stImage"] {
    display: flex;
    justify-content: center;
}

.sidebar-logo-card img {
    width: 100%;
    max-width: none;
    height: auto;
    display: block;
    margin: 0 auto;
    filter: drop-shadow(0 4px 12px rgba(15, 23, 42, 0.28));
}

.sidebar-step-item {
    display: flex;
    align-items: flex-start;
    gap: 0.6rem;
    margin: 0.42rem 0;
    line-height: 1.5;
}

.sidebar-step-badge {
    width: 0.82rem;
    height: 0.82rem;
    border-radius: 999px;
    flex: 0 0 0.82rem;
    margin-top: 0.34rem;
    border: 1px solid rgba(148, 163, 184, 0.34);
    background: rgba(255, 255, 255, 0.08);
}

.sidebar-step-item.done .sidebar-step-badge {
    width: 1.05rem;
    height: 1.05rem;
    flex-basis: 1.05rem;
    margin-top: 0.2rem;
    border: none;
    background: linear-gradient(90deg, #34d399 0%, #10b981 100%);
    position: relative;
}

.sidebar-step-item.done .sidebar-step-badge::after {
    content: "✓";
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 0.72rem;
    font-weight: 900;
}

.sidebar-step-item.current .sidebar-step-badge {
    border: none;
    background: linear-gradient(90deg, #818cf8 0%, #8b5cf6 100%);
    box-shadow: 0 0 0 3px rgba(129, 140, 248, 0.18);
}

.sidebar-step-item.pending .sidebar-step-badge {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(148, 163, 184, 0.22);
}

.sidebar-step-label {
    color: #e5e7eb;
    font-size: 1.02rem;
    font-weight: 700;
}

.sidebar-step-item.current .sidebar-step-label {
    color: #ffffff;
}

.sidebar-step-item.done .sidebar-step-label {
    color: #cbd5e1;
    opacity: 0.92;
}

/* ===== サイドバー調整 ===== */

[data-testid="stSidebar"] [data-testid="stImage"] {
    padding: 0.05rem 0 0.55rem 0;
}

[data-testid="stSidebar"] [data-testid="stImage"] img {
    width: 100% !important;
    max-width: none !important;
    height: auto !important;
    display: block;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #050816 0%, #0b1020 100%);
    border-right: 1px solid rgba(99, 102, 241, 0.18);
}

[data-testid="stSidebar"] * {
    color: #e5e7eb;
}

/* サイドバー内のボタンもメインと同じ思想で分ける */
[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    border: 1px solid rgba(129, 140, 248, 0.24);
    border-radius: 16px;
    padding: 0.72rem 1rem;
    font-weight: 800;
    color: #e5e7eb;
    background: rgba(15, 23, 42, 0.88);
    box-shadow: none;
}

[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    border: none;
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

/* STEP4以降の前提条件カードを見やすくする */
.precondition-card {
    background: linear-gradient(180deg, rgba(15, 23, 42, 0.98) 0%, rgba(17, 24, 39, 0.95) 100%);
    border: 1px solid rgba(99, 102, 241, 0.24);
    border-radius: 20px;
    padding: 1rem 1.15rem;
    margin: 0.25rem 0 0.9rem 0;
    box-shadow: 0 10px 24px rgba(0, 0, 0, 0.16);
}

.precondition-title {
    display: block;
    font-size: 1.02rem;
    font-weight: 800;
    color: #c4b5fd;
    margin-bottom: 0.6rem;
    letter-spacing: 0.01em;
}

.info-block {
    font-size: 1.18rem;
    line-height: 1.9;
    margin-bottom: 0.45rem;
}

.solution-rank-line {
    font-size: 1.18rem;
    font-weight: 800;
    line-height: 1.55;
    color: #f8fafc;
    margin: 0;
}

.rank-badge {
    color: #fde68a;
    font-weight: 900;
}

.score-card {
    background: rgba(15, 23, 42, 0.82);
    border: 1px solid rgba(99, 102, 241, 0.18);
    border-radius: 18px;
    padding: 0.9rem 0.8rem 0.8rem 0.8rem;
    min-height: 138px;
}

.score-card-title {
    font-size: 1.02rem;
    font-weight: 700;
    color: #f8fafc;
    margin-bottom: 0.55rem;
    line-height: 1.4;
}

.score-card-stars {
    font-size: 1.75rem;
    line-height: 1.15;
    color: #f8fafc;
    letter-spacing: 0.03em;
    margin-bottom: 0.45rem;
    white-space: nowrap;
}

.score-card-reason {
    font-size: 0.98rem;
    line-height: 1.6;
    color: #cbd5e1;
}

.lean-grid-card {
    background: linear-gradient(180deg, rgba(15, 23, 42, 0.94) 0%, rgba(17, 24, 39, 0.92) 100%);
    border: 1px solid rgba(99, 102, 241, 0.18);
    border-radius: 20px;
    padding: 1rem 1rem 0.95rem 1rem;
    min-height: 260px;
    margin-bottom: 0.9rem;
}

.lean-card-title {
    font-size: 1.05rem;
    line-height: 1.4;
    font-weight: 800;
    color: #f8fafc;
    margin-bottom: 0.7rem;
}

.sub-section-title {
    font-size: 1.2rem;
    font-weight: 800;
    color: #f8fafc;
    margin: 0 0 0.35rem 0;
}

.lean-card-body {
    font-size: 1.08rem;
    line-height: 1.85;
    color: #d1d5db;
}

.lean-card-body ul {
    margin: 0.2rem 0 0 1.1rem;
    padding: 0;
}

.lean-card-body li {
    margin-bottom: 0.38rem;
}

.info-block:last-child {
    margin-bottom: 0;
}

.precondition-helper {
    font-size: 0.98rem;
    line-height: 1.75;
    color: #94a3b8;
    margin: -0.15rem 0 0.95rem 0.1rem;
}


/* 補足説明・success/info/caption系も少し読みやすくする */
[data-testid="stAlertContainer"] {
    font-size: 1.08rem;
    line-height: 1.8;
}

[data-testid="stAlertContainer"] p,
[data-testid="stAlertContainer"] li {
    font-size: 1.08rem !important;
    line-height: 1.8 !important;
}

.sidebar-footer-note {
    margin-top: 2.2rem;
    padding-top: 1.0rem;
    border-top: 1px solid rgba(148, 163, 184, 0.10);
    color: rgba(203, 213, 225, 0.38);
    font-size: 0.74rem;
    line-height: 1.55;
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
    logo_img = Image.open("logo.png").convert("RGBA")
    logo_bbox = logo_img.getbbox()
    if logo_bbox:
        logo_img = logo_img.crop(logo_bbox)
    st.image(logo_img, use_container_width=True)
    st.markdown("## 仮説設計フロー")

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
            state_class = "done"
        elif i == st.session_state.current_step:
            state_class = "current"
        else:
            state_class = "pending"

        st.markdown(
            f'''
            <div class="sidebar-step-item {state_class}">
                <div class="sidebar-step-badge"></div>
                <div class="sidebar-step-label">{step_name}</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 2.2rem;'></div>", unsafe_allow_html=True)
    st.markdown(
        '<div class="sidebar-footer-note">テクゼロン 新規事業設計支援アプリ v0.2</div>',
        unsafe_allow_html=True,
    )

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
        <div class="page-step-title">① 市場・ターゲットを入力</div>
        <div class="step1-help">分析したい市場やターゲットを入力してください。</div>
        """,
        unsafe_allow_html=True,
    )

    # ★ text_input は label が必須。
    # ★ 画面上では見せたくないので label_visibility="collapsed" で隠す。
    market = st.text_input(
        "市場・ターゲット",
        value=st.session_state.market_input,
        label_visibility="collapsed",
    )

    step1_input_error = False

    # STEP1 の入力例 expander だけ、見出しを少し小さく・太字なしにする
    # ※ このCSSは STEP1 が表示されているときだけ描画されるため、他ステップの expander には影響しない
    st.markdown(
        """
        <style>
        [data-testid="stExpander"] details summary p {
            font-size: 0.96rem !important;
            font-weight: 500 !important;
            line-height: 1.45 !important;
        }
        .stButton > button[kind="primary"] {
            font-weight: 900 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown('<div class="step1-primary-button">', unsafe_allow_html=True)
        if st.button("🔍 分析開始", type="primary", use_container_width=True):
            if market.strip():
                st.session_state.market_input = market.strip()
                st.session_state.current_step = 2
                st.rerun()
            else:
                step1_input_error = True
        st.markdown('</div>', unsafe_allow_html=True)

    if step1_input_error:
        st.warning("市場・ターゲットを入力してください。")
    st.markdown("<div style='height: 0.25rem;'></div>", unsafe_allow_html=True)

    # ★ テクゼロンの事業に合った入力例を提示。
    # ★ ここは「何を書けばいいか分からない」を防ぐための補助エリア。
    with st.expander("💡 入力例を見る（テクゼロンの強みを活かせるテーマ）"):
        st.caption("気になるテーマがあれば押してください。上の入力欄に反映されます。")
        examples = [
            "製造業DX×設備予兆保全サービス",
            "半導体製造の歩留まり改善×AI分析",
            "熟練技能者の暗黙知デジタル承継",
            "産業用ロボットのリモートメンテナンス",
            "工場のスマートファクトリー化×IoTプラットフォーム",
        ]
        for ex in examples:
            if st.button(ex, key=f"ex_{ex}"):
                # ★ 入力例を押したら、そのまま次に進むのではなく、
                #   上の入力欄へ値を反映するだけにする。
                st.session_state.market_input = ex
                st.rerun()


# ============================================================
# STEP 2: 市場分析 (PEST / 5 Forces)
# ============================================================
# ★ st.spinner でローディング表示、st.tabs でタブ切り替え

elif st.session_state.current_step == 2:
    st.markdown('<div class="page-step-title">② 市場分析</div>', unsafe_allow_html=True)

    st.markdown(
        """
        <style>
        [data-testid="stExpander"] details summary p {
            color: #f8fafc !important;
            font-size: 1.18rem !important;
            font-weight: 800 !important;
            line-height: 1.55 !important;
            margin: 0 !important;
        }
        .stButton > button[kind="primary"] {
            font-weight: 800 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(f"**対象市場:** {st.session_state.market_input}")

    # まだ分析していない場合は、まず「分析中」であることを大きく明示する。
    analysis_was_pending = not st.session_state.analysis_done
    if analysis_was_pending:
        st.markdown(
            """
            <div class="analysis-loading-card">
                <div class="analysis-loading-header">
                    <div class="analysis-loading-spinner"></div>
                    <div class="analysis-loading-title">市場分析を実行中です</div>
                </div>
                <div class="analysis-loading-body">分析結果が表示されるまで、少々お待ちください。</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <style>
            /* 市場分析中は、前ステップのexpander残像が見えないように一時的に非表示 */
            [data-testid="stExpander"] {
                display: none !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        pest = run_pest_analysis(st.session_state.market_input)
        five_forces = run_five_forces_analysis(st.session_state.market_input)

        st.session_state.pest_result = pest
        st.session_state.five_forces_result = five_forces
        st.session_state.analysis_done = True
        st.rerun()

    # 分析が始まっていた描画サイクルでは、後続UIを一切描かない。
    if analysis_was_pending:
        st.stop()

    top_action_col1, top_spacer, top_action_col2 = st.columns([1.2, 0.2, 1.2])
    with top_action_col1:
        if st.button("⬅️ 市場・ターゲットを変更する", key="step2_back_top", use_container_width=True, type="tertiary"):
            st.session_state.current_step = 1
            st.session_state.analysis_done = False
            st.session_state.pest_result = None
            st.session_state.five_forces_result = None
            st.rerun()
    with top_action_col2:
        if st.button(
            "➡️ この分析内容で課題の探索へ進む",
            key="step2_next_top",
            type="primary",
            use_container_width=True,
            disabled=not st.session_state.analysis_done,
        ):
            st.session_state.current_step = 3
            st.rerun()

    st.markdown("<div style='height: 0.45rem;'></div>", unsafe_allow_html=True)

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

    # --- 削除: 入力例を見る（テクゼロンの強みを活かせるテーマ） expander（STEP2のみ） ---

    bottom_col1, bottom_spacer, bottom_col2 = st.columns([1.2, 0.2, 1.2])
    with bottom_col1:
        if st.button("⬅️ 市場・ターゲットを変更する", key="step2_back_bottom", use_container_width=True, type="tertiary"):
            st.session_state.current_step = 1
            st.session_state.analysis_done = False
            st.session_state.pest_result = None
            st.session_state.five_forces_result = None
            st.rerun()
    with bottom_col2:
        if st.button("➡️ この分析内容で課題の探索へ進む", key="step2_next_bottom", type="primary", use_container_width=True, disabled=not st.session_state.analysis_done):
            st.session_state.current_step = 3
            st.rerun()


# ============================================================
# STEP 3: 課題の探索
# ============================================================
# ★ ボタンで AI 呼び出し → 結果をリスト表示 → 選択ボタンで次へ

elif st.session_state.current_step == 3:
    st.markdown('<div class="page-step-title">③ 課題の探索</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="precondition-card">
            <div class="precondition-title">課題探索の前提条件</div>
            <div class="info-block"><strong>対象市場:</strong> {st.session_state.market_input}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="precondition-helper">この市場分析結果を前提に、AIがテクゼロンの技術資産を踏まえた課題を10個ずつ生成します。納得できるまで何度でも再生成できます。</div>',
        unsafe_allow_html=True,
    )

    # ★ 初回状態では「市場分析へ戻る」と「課題を生成する」を同じ段に並べる。
    # ★ これにより、次の主操作と前のステップへの戻り操作がすぐ分かる。
    if not st.session_state.issues:
        top_action_col1, top_spacer, top_action_col2 = st.columns([1.2, 0.2, 1.2])

        with top_action_col1:
            if st.button("⬅️ 市場・ターゲット分析へ戻る", key="step3_back_top", use_container_width=True, type="tertiary"):
                st.session_state.current_step = 2
                st.rerun()

        with top_action_col2:
            if st.button("🔄 課題を生成する", key="step3_generate_initial", type="primary", use_container_width=True):
                existing = [iss["issue"] for iss in st.session_state.issues]
                with st.spinner("課題を生成中..."):
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

        selected_issue_id = st.session_state.selected_issue.get("id") if st.session_state.selected_issue else None

        for iss in st.session_state.issues:
            with st.container():
                # ★ カードを比較しながら選べるように、
                #   ここでは即遷移せず「選択状態だけ」を保持する。
                card_class = "issue-card selected" if selected_issue_id == iss["id"] else "issue-card"

                st.markdown(
                    f"""
                    <div class="{card_class}">
                        <div class="issue-title">
                            <span class="issue-number">{iss['id']}.</span>課題: {iss.get('issue', '')}
                        </div>
                        <div class="issue-persona">ペルソナ: {iss.get('target', '')}</div>
                        <div class="issue-detail">{iss.get('detail', '')}</div>
                        {"<div class='issue-selected-note'>選択中</div>" if selected_issue_id == iss["id"] else ""}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                action_col1, action_col2 = st.columns([1.7, 4.3])

                with action_col1:
                    if selected_issue_id == iss["id"]:
                        # ★ 選択済みカードの直下にある「次へ進む」は、その場の主操作なので primary に戻す。
                        # ★ 代わりに「さらに10個生成」の優先度を落として、誤操作を減らす。
                        if st.button("この課題を選ぶ", key=f"go_issue_{iss['id']}", use_container_width=True, type="primary"):
                            st.session_state.current_step = 4
                            st.rerun()
                    else:
                        if st.button("選択", key=f"sel_issue_{iss['id']}", use_container_width=True):
                            st.session_state.selected_issue = iss
                            st.rerun()

                with action_col2:
                    st.empty()

                st.divider()

        # ★ カードで選択状態を保持したうえで、下部のCTAから明示的に次へ進む。
        # ★ これにより、複数カードを比較してから決めやすくする。
        bottom_col1, spacer, bottom_col2 = st.columns([1.2, 0.2, 1.2])

        with bottom_col1:
            if st.button("⬅️ 市場・ターゲット分析へ戻る", key="step3_back_bottom", use_container_width=True, type="tertiary"):
                st.session_state.current_step = 2
                st.rerun()

        with bottom_col2:
            # ★ 「さらに10個生成」は補助操作なので secondary にして主張を下げる。
            if st.button("🔄 さらに10個生成", use_container_width=True):
                existing = [iss["issue"] for iss in st.session_state.issues]
                with st.spinner("課題を生成中..."):
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


# ============================================================
# STEP 4: 解決策の生成
# ============================================================
# ★ rank_solutions() でソート → st.expander + st.columns でスコア表示

elif st.session_state.current_step == 4:
    st.markdown('<div class="page-step-title">④ 解決策の生成</div>', unsafe_allow_html=True)

    issue = st.session_state.selected_issue
    st.markdown(
        f"""
        <div class="precondition-card">
            <div class="precondition-title">解決策生成の前提条件</div>
            <div class="info-block"><strong>対象市場:</strong> {st.session_state.market_input}</div>
            <div class="info-block"><strong>選択課題:</strong> {issue.get("issue", "")}</div>
            <div class="info-block"><strong>ペルソナ:</strong> {issue.get("target", "")}<br>{issue.get("detail", "")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ★ 初回状態では「戻る」と「解決策を生成する」を同じ横幅・同じ段に並べる。
    # ★ これにより、どちらが主要操作でどちらが補助操作かが見やすくなる。
    if not st.session_state.solutions:
        top_action_col1, spacer, top_action_col2 = st.columns([1.2, 0.2, 1.2])

        with top_action_col1:
            if st.button("課題選択に戻る", use_container_width=True, type="tertiary", key="step4_back_initial"):
                st.session_state.current_step = 3
                st.session_state.solutions = []
                st.rerun()

        with top_action_col2:
            if st.button("💡 解決策を生成する", type="primary", use_container_width=True, key="step4_generate_initial"):
                existing = [s["title"] for s in st.session_state.solutions]
                with st.spinner("🔄 解決策を生成中..."):
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
        st.markdown(
            f'<div class="sub-section-title">🏆 解決策ランキング（{len(ranked)}件）</div>',
            unsafe_allow_html=True,
        )

        for sol in ranked:
            scoring = sol.get("scoring", {})
            total = scoring.get("total", 0)

            rank_header = f"{sol['rank']}位｜{sol.get('title', '')}　⭐{total}/25"

            with st.expander(
                rank_header,
                expanded=(sol["rank"] <= 3),
            ):
                tech_used = sol.get("tech_used", "")
                if tech_used:
                    st.caption(f"活用技術: {tech_used}")
                st.markdown(sol.get("description", ""))

                st.markdown("---")
                st.markdown("**📊 スコアリング詳細:**")

                score_cols = st.columns(5)
                for idx, (key, label) in enumerate(SCORING_AXES):
                    axis = scoring.get(key, {})
                    with score_cols[idx]:
                        raw_score = axis.get("score", 0)

                        # AI出力ゆれ対策:
                        # score が数値ではなく dict で返るケースでも落ちないようにする
                        if isinstance(raw_score, dict):
                            raw_score = raw_score.get("value", raw_score.get("score", 0))

                        try:
                            s = int(float(raw_score))
                        except (TypeError, ValueError):
                            s = 0

                        # 星表示の崩れ防止
                        s = max(0, min(5, s))
                        stars = f"{'★' * s}{'☆' * (5-s)}"
                        st.markdown(
                            f"""
                            <div class="score-card">
                                <div class="score-card-title">{label}</div>
                                <div class="score-card-stars">{stars}</div>
                                <div class="score-card-reason">{axis.get('reason', '')}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                st.divider()

                if st.button("✅ この解決策でリーンキャンバスへ", key=f"sel_sol_{sol['id']}", type="primary", use_container_width=True):
                    st.session_state.selected_solution = sol
                    st.session_state.current_step = 5
                    st.rerun()
    else:
        pass

    if st.session_state.solutions:
        bottom_col1, spacer, bottom_col2 = st.columns([1.2, 0.2, 1.2])

        with bottom_col1:
            if st.button("⬅️ 課題選択に戻る", use_container_width=True, type="tertiary", key="step4_back_after_generated"):
                st.session_state.current_step = 3
                st.session_state.solutions = []
                st.rerun()

        with bottom_col2:
            if st.button("🔄 さらに10個生成", use_container_width=True, key="step4_generate_more"):
                existing = [s["title"] for s in st.session_state.solutions]
                with st.spinner("🔄 解決策を生成中..."):
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


# ============================================================
# STEP 5: リーンキャンバス ★ 新規追加！
# ============================================================
# ★ AIが生成した9ブロックのリーンキャンバスを表示

elif st.session_state.current_step == 5:
    st.markdown('<div class="page-step-title">⑤ リーンキャンバス</div>', unsafe_allow_html=True)

    sol = st.session_state.selected_solution
    issue = st.session_state.selected_issue
    st.markdown(
        f"""
        <div class="precondition-card">
            <div class="precondition-title">リーンキャンバス作成の前提条件</div>
            <div class="info-block"><strong>対象市場:</strong> {st.session_state.market_input}</div>
            <div class="info-block"><strong>選択課題:</strong> {issue.get('issue', '')}</div>
            <div class="info-block"><strong>選択した解決策:</strong> {sol.get('title', '')}<br>{sol.get('description', '')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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
        st.markdown('<div class="sub-section-title">📋 リーンキャンバス</div>', unsafe_allow_html=True)

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

        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ 解決策選択に戻る", use_container_width=True):
                st.session_state.current_step = 4
                st.session_state.lean_canvas_result = None
                st.rerun()

        with col2:
            if st.button("➡️ チーム編成へ進む", type="primary", use_container_width=True):
                st.session_state.current_step = 6
                st.rerun()


# ============================================================
# STEP 6: チーム編成
# ============================================================
# ★ build_team_for_solution() → メンバー横並び表示 → MBTI相性コメント

elif st.session_state.current_step == 6:
    st.markdown('<div class="page-step-title">⑥ 最適チーム編成</div>', unsafe_allow_html=True)

    sol = st.session_state.selected_solution
    issue = st.session_state.selected_issue
    st.markdown(
        f"""
        <div class="precondition-card">
            <div class="precondition-title">チーム編成の前提条件</div>
            <div class="info-block"><strong>対象市場:</strong> {st.session_state.market_input}</div>
            <div class="info-block"><strong>選択課題:</strong> {issue.get('issue', '')}</div>
            <div class="info-block"><strong>選択した解決策:</strong> {sol.get('title', '')}<br>{sol.get('description', '')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height: 0.15rem;'></div>", unsafe_allow_html=True)

    if st.session_state.team_result is None:
        st.markdown(
            """
            <div class="team-loading-card">
                <div class="team-loading-header">
                    <div class="team-loading-spinner"></div>
                    <div class="team-loading-title">チーム編成を実行中です</div>
                </div>
                <div class="team-loading-body">テクゼロン社員の強み・役割・相性をもとに、最適な4人チームを選抜しています。少々お待ちください。</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        team_data = build_team_for_solution(
            sol.get("title", ""),
            sol.get("description", ""),
        )
        st.session_state.team_result = team_data
        st.rerun()


    team_data = st.session_state.team_result

    if team_data and "error" not in team_data:
        team = team_data.get("team", [])

        st.markdown('<div class="sub-section-title" style="margin-top:-0.1rem;">👥 プロジェクトチーム</div>', unsafe_allow_html=True)

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
            st.markdown('<div class="sub-section-title">🤝 チームシナジー</div>', unsafe_allow_html=True)
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
            st.markdown('<div class="sub-section-title">⚠️ 想定リスクと対策</div>', unsafe_allow_html=True)
            st.markdown(team_data.get("team_risk", ""))

        st.divider()

        # セッション保存 & ナビゲーション
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("⬅️ リーンキャンバスに戻る", use_container_width=True, type="tertiary"):
                st.session_state.current_step = 5
                st.session_state.team_result = None
                st.rerun()

        with col2:
            if st.button("🔄 別のチーム編成を試す", use_container_width=True):
                st.session_state.team_result = None
                st.rerun()

        with col3:
            if st.button("💾 この結果を保存", use_container_width=True, type="primary"):
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
    else:
        st.error(f"チーム編成でエラーが発生しました: {team_data.get('error', '不明')}")
        if st.button("🔄 再試行"):
            st.session_state.team_result = None
            st.rerun()
