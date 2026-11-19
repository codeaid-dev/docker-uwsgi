import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "quiz.db"
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # 外部キー制約を有効にする
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def initialize_database():
    with get_connection() as conn:
        # categoriesテーブル
        conn.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        """)
        # questionsテーブル
        conn.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                choice1 TEXT NOT NULL,
                choice2 TEXT NOT NULL,
                choice3 TEXT NOT NULL,
                choice4 TEXT NOT NULL,
                correct_answer INTEGER NOT NULL
                    CHECK(correct_answer BETWEEN 1 AND 4),
                explanation TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (category_id)
                    REFERENCES categories(id)
            )
        """)
        # wrong_answersテーブル
        # 今回はテーブルのみ作成し、管理機能は実装しない
        conn.execute("""
            CREATE TABLE IF NOT EXISTS wrong_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL UNIQUE,
                wrong_count INTEGER NOT NULL DEFAULT 1,
                last_wrong_at TEXT,
                is_reviewed INTEGER NOT NULL DEFAULT 0,

                FOREIGN KEY (question_id)
                    REFERENCES questions(id)
                    ON DELETE CASCADE
            )
        """)
        # 初期カテゴリ
        categories = [
            "Java",
            "SQL",
            "Servlet/JSP"
        ]
        for name in categories:
            conn.execute("""
                INSERT OR IGNORE INTO categories (name)
                VALUES (?)
            """, (name,))
        # カテゴリIDを取得
        category_rows = conn.execute("""
            SELECT id, name
            FROM categories
        """).fetchall()
        category_map = {
            row["name"]: row["id"]
            for row in category_rows
        }
        # 初期問題
        questions = [
            (
                category_map["Java"],
                "Javaのコンパイル後のファイルの拡張子は？",
                ".java",
                ".class",
                ".jar",
                ".exe",
                2,
                "Javaのソースファイル（.java）はコンパイルすると"
                ".classファイルになります。"
            ),
            (
                category_map["SQL"],
                "データを検索するときに使用するSQL命令は？",
                "INSERT",
                "UPDATE",
                "SELECT",
                "DELETE",
                3,
                "SELECTはテーブルからデータを検索するSQL命令です。"
            ),
            (
                category_map["Servlet/JSP"],
                "HttpServletでGETリクエストを処理するメソッドは？",
                "doPost()",
                "doGet()",
                "service()",
                "init()",
                2,
                "GETリクエストは通常doGet()メソッドで処理します。"
            )
        ]
        for q in questions:
            conn.execute("""
                INSERT INTO questions (
                    category_id,
                    question,
                    choice1,
                    choice2,
                    choice3,
                    choice4,
                    correct_answer,
                    explanation
                )
                SELECT ?, ?, ?, ?, ?, ?, ?, ?
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM questions
                    WHERE category_id = ?
                      AND question = ?
                )
            """, q + (q[0], q[1]))
