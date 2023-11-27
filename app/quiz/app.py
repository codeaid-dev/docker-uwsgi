from flask import Flask, render_template, request, session
import os, sqlite3, logging
from contextlib import closing
import random
from datetime import timedelta
import mysql.connector

app = Flask(__name__)
app.secret_key = 'Msd4EsJIk6AoVD3g' #セッション情報を暗号化するためのキー
app.permanent_session_lifetime = timedelta(minutes=10) #セッション有効期限10分
base_path = os.path.dirname(__file__)
db_path = base_path + '/quiz.db'

debug_handler = logging.FileHandler('debug.log')
debug_handler.setLevel(logging.DEBUG)
app.logger.addHandler(debug_handler)
error_handler = logging.FileHandler('error.log')
error_handler.setLevel(logging.ERROR)
app.logger.addHandler(error_handler)
app.logger.setLevel(logging.DEBUG)

def create_db():
    try:
        with closing(mysql.connector.connect(user='root', password='password',
                                host='mysql', database='quiz')) as con: #MySQL
        #with closing(sqlite3.connect(db_path)) as con: #SQLite
            cur = con.cursor(prepared=True,dictionary=True) #MySQL
            #cur = con.cursor() #SQLite
            #For SQLite using AUTOINCREMENT, for MySQL using AUTO_INCREMENT
            cur.execute('''CREATE TABLE IF NOT EXISTS questions (
            id INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,
            question VARCHAR(255) NOT NULL,
            answer VARCHAR(255) NOT NULL
            )''')
    except sqlite3.Error as e:
        app.logger.error(e)
create_db()

def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

def exec(sql, *arg):
    try:
        with closing(mysql.connector.connect(user='root', password='password',
                                host='mysql', database='quiz')) as con: #MySQL
        #with closing(sqlite3.connect(db_path)) as con: #SQLite
            con.row_factory = dict_factory
            cur = con.cursor(prepared=True,dictionary=True) #MySQL
            #cur = con.cursor() #SQLite
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

        if not info:
            if values['id'].isdigit():
                if 'edit' in request.form: # 修正ボタンが押された
                    if values['question'] and values['answer']:
                        exec('UPDATE questions SET question=?, answer=? WHERE id=?', values['question'], values['answer'], values['id'])
                        info = f"番号{values['id']}を修正しました。"
                        quizlist = exec('SELECT * FROM questions')
                    else:
                        info = '問題か答えが空白です。'
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

@app.route('/quiz/', methods=['GET','POST'])
def quiz():
    result = None
    if request.method == 'POST':
        question = session['question'] if 'question' in session else {}
        if 'answer' in request.form:
            if request.form['answer'] == question['answer']:
                result = '正解です'
            else:
                result = f"不正解です(正解：{question['answer']})"
    else:
        res = exec('SELECT * FROM questions')
        if res:
            question = random.choice(res)
            session['question'] = question
        else:
            question = None

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
    app.run(debug=True)
