"""
database.py — SQLite データベース操作モジュール
================================================
【担当】DB担当
【役割】SQLiteへの接続管理、社員データの取得、セッションログの保存を行う。
        参考アプリの database.py に相当する。

このモジュールは schema.sql で定義されたテーブルに対して CRUD 操作を提供する。
"""

import json
import sqlite3
from pathlib import Path

DB_PATH = Path("data/tech0_hr.db")


# ---------- 接続管理 ---------- #


def get_connection() -> sqlite3.Connection:
    """
    SQLite データベースへの接続を返す。
    - data/ フォルダがなければ自動作成
    - Row を dict 風に使えるようにする
    """
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    schema.sql を実行してテーブルを初期化する。
    既にテーブルがある場合は何もしない（IF NOT EXISTS）。
    テーブル作成後、社員データが0件なら自動で seed を実行する。
    """
    conn = get_connection()
    with open("schema.sql", "r", encoding="utf-8") as f:
        conn.executescript(f.read())

    # 社員データが空なら自動投入
    cursor = conn.execute("SELECT COUNT(*) FROM employees")
    count = cursor.fetchone()[0]
    conn.close()

    if count == 0:
        from seed_data import seed
        seed()


# ---------- 社員データ取得 ---------- #


def get_all_employees() -> list[dict]:
    """
    全社員データを取得して dict のリストで返す。
    マッチングエンジンに渡すために使う。
    """
    conn = get_connection()
    cursor = conn.execute("SELECT * FROM employees ORDER BY id")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_employee_by_id(employee_id: int) -> dict | None:
    """
    社員IDで1名分のデータを取得する。
    """
    conn = get_connection()
    cursor = conn.execute("SELECT * FROM employees WHERE id = ?", (employee_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_employees_by_ids(ids: list[int]) -> list[dict]:
    """
    複数の社員IDでデータを取得する。
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
    """
    conn = get_connection()
    cursor = conn.execute(
        "SELECT * FROM employees WHERE skills LIKE ?", (f"%{skill}%",)
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


# ---------- セッションログ ---------- #


def save_session_log(
    market_input: str,
    pest_result: dict | None = None,
    five_forces_result: dict | None = None,
    selected_issue: str | None = None,
    selected_solution: str | None = None,
    team_members: list | None = None,
) -> int:
    """
    1回のセッション結果をログとして保存する。

    Returns:
        int: 挿入されたログのID
    """
    conn = get_connection()
    cursor = conn.execute(
        """
        INSERT INTO session_logs
            (market_input, pest_result, five_forces_result,
             selected_issue, selected_solution, team_members)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            market_input,
            json.dumps(pest_result, ensure_ascii=False) if pest_result else None,
            json.dumps(five_forces_result, ensure_ascii=False) if five_forces_result else None,
            selected_issue,
            selected_solution,
            json.dumps(team_members, ensure_ascii=False) if team_members else None,
        ),
    )
    conn.commit()
    log_id = cursor.lastrowid
    conn.close()
    return log_id


# ---------- テスト用 ---------- #

if __name__ == "__main__":
    init_db()
    employees = get_all_employees()
    print(f"社員数: {len(employees)}")
    for emp in employees[:3]:
        print(f"  {emp['name']} ({emp['department']}) - MBTI: {emp['mbti']}")
