import random
import sqlite3

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from database import get_connection, initialize_database

app = Flask(__name__)
# セッション用の秘密鍵
app.secret_key = "change-this-secret-key"

# --------------------------------
# 共通処理
# --------------------------------
def get_categories():
    with get_connection() as conn:
        return conn.execute("""
            SELECT *
            FROM categories
            ORDER BY id
        """).fetchall()

def get_questions():
    with get_connection() as conn:
        return conn.execute("""
            SELECT
                q.*,
                c.name AS category_name
            FROM questions q
            INNER JOIN categories c
                ON q.category_id = c.id
            ORDER BY q.id DESC
        """).fetchall()

def get_question(question_id):
    with get_connection() as conn:
        return conn.execute("""
            SELECT *
            FROM questions
            WHERE id = ?
        """, (question_id,)).fetchone()

def validate_question(data):
    errors = []
    # カテゴリ
    try:
        category_id = int(data.get("category_id", ""))
    except (ValueError, TypeError):
        category_id = 0
    with get_connection() as conn:
        category = conn.execute("""
            SELECT id
            FROM categories
            WHERE id = ?
        """, (category_id,)).fetchone()
    if category is None:
        errors.append("カテゴリを正しく選択してください。")
    # 問題文
    question = data.get("question", "").strip()
    if not question:
        errors.append("問題文を入力してください。")
    elif len(question) > 500:
        errors.append("問題文は500文字以内で入力してください。")
    # 選択肢
    choices = []
    for i in range(1, 5):
        choice = data.get(f"choice{i}", "").strip()
        choices.append(choice)
        if not choice:
            errors.append(f"選択肢{i}を入力してください。")
        elif len(choice) > 200:
            errors.append(f"選択肢{i}は200文字以内にしてください。")
    # 正解番号
    try:
        correct_answer = int(data.get("correct_answer", ""))
    except (ValueError, TypeError):
        correct_answer = 0
    if correct_answer not in (1, 2, 3, 4):
        errors.append("正解を1～4から選択してください。")
    # 解説
    explanation = data.get("explanation", "").strip()
    if not explanation:
        errors.append("解説を入力してください。")
    elif len(explanation) > 2000:
        errors.append("解説は2000文字以内にしてください。")
    values = {
        "category_id": category_id,
        "question": question,
        "choice1": choices[0],
        "choice2": choices[1],
        "choice3": choices[2],
        "choice4": choices[3],
        "correct_answer": correct_answer,
        "explanation": explanation
    }
    return errors, values

# --------------------------------
# 問題一覧
# --------------------------------
@app.route("/")
def index():
    questions = get_questions()
    return render_template(
        "list.html",
        questions=questions
    )

# --------------------------------
# 問題登録
# --------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    categories = get_categories()
    if request.method == "POST":
        errors, values = validate_question(request.form)
        if not errors:
            with get_connection() as conn:
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
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    values["category_id"],
                    values["question"],
                    values["choice1"],
                    values["choice2"],
                    values["choice3"],
                    values["choice4"],
                    values["correct_answer"],
                    values["explanation"]
                ))
            flash("問題を登録しました。")
            return redirect(url_for("index"))
        return render_template(
            "form.html",
            title="問題登録",
            categories=categories,
            values=values,
            errors=errors
        )

    values = {
        "category_id": "",
        "question": "",
        "choice1": "",
        "choice2": "",
        "choice3": "",
        "choice4": "",
        "correct_answer": 1,
        "explanation": ""
    }

    return render_template(
        "form.html",
        title="問題登録",
        categories=categories,
        values=values,
        errors=[]
    )

# --------------------------------
# 問題編集
# --------------------------------
@app.route("/edit/<int:question_id>", methods=["GET", "POST"])
def edit(question_id):
    question = get_question(question_id)
    if question is None:
        flash("対象の問題がありません。")
        return redirect(url_for("index"))
    categories = get_categories()
    if request.method == "POST":
        errors, values = validate_question(request.form)
        if not errors:
            with get_connection() as conn:
                conn.execute("""
                    UPDATE questions
                    SET
                        category_id = ?,
                        question = ?,
                        choice1 = ?,
                        choice2 = ?,
                        choice3 = ?,
                        choice4 = ?,
                        correct_answer = ?,
                        explanation = ?
                    WHERE id = ?
                """, (
                    values["category_id"],
                    values["question"],
                    values["choice1"],
                    values["choice2"],
                    values["choice3"],
                    values["choice4"],
                    values["correct_answer"],
                    values["explanation"],
                    question_id
                ))

            flash("問題を更新しました。")
            return redirect(url_for("index"))
        return render_template(
            "form.html",
            title="問題編集",
            categories=categories,
            values=values,
            errors=errors
        )
    return render_template(
        "form.html",
        title="問題編集",
        categories=categories,
        values=dict(question),
        errors=[]
    )

# --------------------------------
# 問題削除
# --------------------------------
@app.route("/delete/<int:question_id>", methods=["POST"])
def delete(question_id):
    with get_connection() as conn:
        conn.execute("""
            DELETE FROM questions
            WHERE id = ?
        """, (question_id,))

    flash("問題を削除しました。")
    return redirect(url_for("index"))

# --------------------------------
# クイズ開始
# --------------------------------
@app.route("/quiz/start", methods=["GET", "POST"])
def quiz_start():
    if request.method == "POST":
        try:
            count = int(request.form.get("question_count", ""))
        except (ValueError, TypeError):
            count = 0
        if count < 1 or count > 50:
            flash("出題数は1～50で指定してください。")
            return redirect(url_for("quiz_start"))
        with get_connection() as conn:
            all_questions = conn.execute("""
                SELECT *
                FROM questions
            """).fetchall()
        total_count = len(all_questions)
        if total_count == 0:
            flash("出題できる問題がありません。")
            return redirect(url_for("quiz_start"))
        if count > total_count:
            flash(
                f"出題数は{total_count}問以下にしてください。"
            )
            return redirect(url_for("quiz_start"))
        # Python側でランダムに並べ替える
        all_questions = list(all_questions)
        random.shuffle(all_questions)
        # 指定数だけ取り出す
        selected_questions = all_questions[:count]
        session["quiz"] = {
            "questions": [
                dict(q) for q in selected_questions
            ],
            "current": 0,
            "correct_count": 0,
            "answer": None
        }
        return redirect(url_for("quiz_question"))
    return render_template("quiz_start.html")

# --------------------------------
# 問題表示
# --------------------------------
@app.route("/quiz/question")
def quiz_question():
    quiz = session.get("quiz")
    if quiz is None:
        return redirect(url_for("quiz_start"))
    current = quiz["current"]
    questions = quiz["questions"]
    if current >= len(questions):
        return redirect(url_for("quiz_complete"))
    # すでに回答済みなら結果画面へ
    if quiz["answer"] is not None:
        return redirect(url_for("quiz_result"))
    question = questions[current]
    return render_template(
        "quiz_question.html",
        question=question,
        current=current + 1,
        total=len(questions)
    )

# --------------------------------
# 回答処理
# --------------------------------
@app.route("/quiz/answer", methods=["POST"])
def quiz_answer():
    quiz = session.get("quiz")
    if quiz is None:
        return redirect(url_for("quiz_start"))
    if quiz["answer"] is not None:
        return redirect(url_for("quiz_result"))
    try:
        answer = int(request.form.get("answer", ""))
    except (ValueError, TypeError):
        flash("回答を選択してください。")
        return redirect(url_for("quiz_question"))
    if answer not in (1, 2, 3, 4):
        flash("回答が正しくありません。")
        return redirect(url_for("quiz_question"))
    question = quiz["questions"][quiz["current"]]
    correct = answer == question["correct_answer"]
    if correct:
        quiz["correct_count"] += 1
    quiz["answer"] = {
        "selected": answer,
        "is_correct": correct
    }
    session["quiz"] = quiz
    return redirect(url_for("quiz_result"))

# --------------------------------
# 回答結果
# --------------------------------
@app.route("/quiz/result")
def quiz_result():
    quiz = session.get("quiz")
    if quiz is None or quiz["answer"] is None:
        return redirect(url_for("quiz_question"))
    question = quiz["questions"][quiz["current"]]
    return render_template(
        "quiz_result.html",
        question=question,
        answer=quiz["answer"],
        current=quiz["current"] + 1,
        total=len(quiz["questions"])
    )

# --------------------------------
# 次の問題
# --------------------------------
@app.route("/quiz/next", methods=["POST"])
def quiz_next():
    quiz = session.get("quiz")
    if quiz is None or quiz["answer"] is None:
        return redirect(url_for("quiz_question"))
    quiz["current"] += 1
    quiz["answer"] = None
    session["quiz"] = quiz
    if quiz["current"] >= len(quiz["questions"]):
        return redirect(url_for("quiz_complete"))
    return redirect(url_for("quiz_question"))

# --------------------------------
# クイズ終了
# --------------------------------
@app.route("/quiz/complete")
def quiz_complete():
    quiz = session.get("quiz")
    if quiz is None:
        return redirect(url_for("index"))
    total = len(quiz["questions"])
    correct = quiz["correct_count"]
    percentage = round(correct / total * 100, 1) if total else 0
    return render_template(
        "quiz_complete.html",
        total=total,
        correct=correct,
        percentage=percentage
    )

# --------------------------------
# クイズ終了処理
# --------------------------------
@app.route("/quiz/finish", methods=["POST"])
def quiz_finish():
    session.pop("quiz", None)
    flash("クイズを終了しました。")
    return redirect(url_for("index"))

# --------------------------------
# アプリ起動
# --------------------------------
initialize_database()

if __name__ == "__main__":
    app.run(debug=True)
