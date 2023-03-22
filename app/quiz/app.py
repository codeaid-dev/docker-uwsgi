from flask import Flask, render_template, request, redirect, url_for
import os, sqlite3, logging
from contextlib import closing
import random

app = Flask(__name__)
base_path = os.path.dirname(__file__)
db_path = base_path + '/quiz.db'
question = None

debug_handler = logging.FileHandler('debug.log')
debug_handler.setLevel(logging.DEBUG)
app.logger.addHandler(debug_handler)
error_handler = logging.FileHandler('error.log')
error_handler.setLevel(logging.ERROR)
app.logger.addHandler(error_handler)
app.logger.setLevel(logging.DEBUG)

def create_db():
    try:
        with closing(sqlite3.connect(db_path)) as con:
            cur = con.cursor()
            cur.execute('''CREATE TABLE IF NOT EXISTS questions (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            question VARCHAR(255) NOT NULL,
            answer VARCHAR(255) NOT NULL
            )''')
    except sqlite3.Error as e:
        app.logger.error(e)

def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

def exec(sql, *arg):
    try:
        with closing(sqlite3.connect(db_path)) as con:
            con.row_factory = dict_factory
            cur = con.cursor()
            cur.execute(sql, arg)
            res = None
            if sql.lstrip().upper().startswith('SELECT'):
                res = cur.fetchall()
            con.commit()
    except sqlite3.Error as e:
        app.logger.error(e)
    return res

@app.route('/')
def index():
    create_db()
    return render_template('index.html', title='クイズ作成と出題')

@app.route('/edit', methods=['GET','POST'])
def edit():
    info = ''
    values = {'id':'','question':'','answer':''}
    values['id'] = request.form['id'] if 'id' in request.form else ''
    values['question'] = request.form['question'] if 'question' in request.form else ''
    values['answer'] = request.form['answer'] if 'answer' in request.form else ''
    quizlist = exec('SELECT * FROM questions')
    if request.method == 'POST':
        for q in quizlist:
            if str(q['id']) == values['id']:
                break
        else:
            info = '指定した番号はありません。'

        if values['id'].isdigit():
            if 'edit' in request.form: # 修正ボタンが押された
                exec('UPDATE questions SET question=?, answer=? WHERE id=?', values['question'], values['answer'], values['id'])
                info = f"番号{values['id']}を修正しました。"
                quizlist = exec('SELECT * FROM questions')
            if 'delete' in request.form: # 削除ボタンが押された
                exec('DELETE FROM questions WHERE id=?', values['id'])
                info = f"番号{values['id']}を削除しました。"
                quizlist = exec('SELECT * FROM questions')
            if 'get' in request.form: # 読込ボタンが押された
                res = exec('SELECT * FROM questions WHERE id=?', values['id'])
                if res:
                    values['question'] = res[0]['question']
                    values['answer'] = res[0]['answer']
        else:
            info = '番号は数字で入力してください。'
    return render_template('edit.html', title='クイズ編集', info=info, values=values, quizlist=quizlist)

@app.route('/quiz', methods=['GET','POST'])
def quiz():
    global question
    result = None
    if request.method == 'POST':
        if 'answer' in request.form:
            if request.form['answer'] == question['answer']:
                result = '正解です'
            else:
                result = f"不正解です(正解：{question['answer']})"
    else:
        res = exec('SELECT * FROM questions')
        question = random.choice(res)

    return render_template('quiz.html', title='クイズ出題', values=question, result=result)

@app.route('/save', methods=['GET','POST'])
def save():
    values = {'question':'','answer':''}
    if request.method == 'POST':
        if 'question' in request.form:
            values['question'] = request.form['question']
        if 'answer' in request.form:
            values['answer'] = request.form['answer']
        exec('INSERT INTO questions (question, answer) VALUES (?,?)', values['question'], values['answer'])
        result = '保存できました。'
        return render_template('save.html', title='クイズ新規作成', values=values, result=result)
    else:
        return render_template('save.html', title='クイズ新規作成', values=values)

if __name__ == '__main__':
    app.run(port=8000, debug=True)
