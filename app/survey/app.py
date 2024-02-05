from flask import Flask, render_template, request, redirect, url_for, session, send_file
import os, sqlite3, hashlib, re, csv
from datetime import timedelta
from contextlib import closing
from werkzeug.security import check_password_hash, generate_password_hash
import mysql.connector
import random, string

app = Flask(__name__)
app.secret_key = ''.join(random.choices(string.ascii_letters + string.digits, k=16)) #セッション情報を暗号化するためのキー
app.permanent_session_lifetime = timedelta(seconds=60) #セッション有効期限60秒
base_path = os.path.dirname(__file__)
db_path = base_path + '/static/survey.db'
csv_path = base_path + '/static/download.csv'
def create_db():
    try:
        with closing(mysql.connector.connect(user='root', password='password',
                                host='mysql', database='survey')) as con: #MySQL
        #with closing(sqlite3.connect(db_path)) as con: #SQLite
            cur = con.cursor()
            cur.execute('''CREATE TABLE IF NOT EXISTS siteadmin (
                username VARCHAR(256) NOT NULL PRIMARY KEY,
                password VARCHAR(256) NOT NULL
                )''')
            #MySQL
            cur.execute('''CREATE TABLE IF NOT EXISTS answers (
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                name VARCHAR(256) NOT NULL,
                email VARCHAR(256) NOT NULL PRIMARY KEY,
                age VARCHAR(256) NOT NULL,
                program VARCHAR(256),
                pc VARCHAR(256) NOT NULL,
                maker VARCHAR(256) NOT NULL,
                comments VARCHAR(256)
                )''')
            #SQLite
            #cur.execute('''CREATE TABLE IF NOT EXISTS answers (
            #    created_at DATETIME DEFAULT (DATETIME('now','localtime')),
            #    name VARCHAR(256) NOT NULL,
            #    email VARCHAR(256) NOT NULL PRIMARY KEY,
            #    age VARCHAR(256) NOT NULL,
            #    program VARCHAR(256),
            #    pc VARCHAR(256) NOT NULL,
            #    maker VARCHAR(256) NOT NULL,
            #    comments VARCHAR(256)
            #    )''')
    except sqlite3.Error as e:
        app.logger.error(e)
create_db()

def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

def exec(sql, *arg):
    try:
        with closing(mysql.connector.connect(user='root', password='password',
                                host='mysql', database='survey')) as con: #MySQL
        #with closing(sqlite3.connect(db_path)) as con:
            con.row_factory = dict_factory
            cur = con.cursor(prepared=True,dictionary=True) #MySQL
            #cur = con.cursor() #SQLite
            if not arg:
                cur.execute(sql)
            else:
                cur.execute(sql, arg)
            res = None
            if sql.lstrip().upper().startswith('SELECT'):
                res = cur.fetchall()
            con.commit()
    except mysql.connector.Error as e: #MySQL
    #except sqlite3.Error as e: #SQLite
        app.logger.error(e)
    return res

def to_hash(password):
    password += 'uMoJL3h90SenH7:r' #SALTを加える
    text = password.encode('utf-8')
    hash = hashlib.sha256(text).hexdigest()
    return hash

def has_email(email):
    sql = 'SELECT * FROM answers WHERE email=?'
    result = exec(sql, email)
    if result:
        return True
    return False

@app.route('/survey/', methods=['GET', 'POST'])
def index():
    postdata = {'name':'','email':'','age':'','program':{},'pc':'','maker':[],'comments':''}
    makers = ['Lenovo','DELL','HP','Apple','Dynabook','NEC','VAIO','ASUS','自作','その他']
    errors = []
    if request.method == 'POST':
        postdata['name'] = request.form['name'] if 'name' in request.form else ''
        postdata['email'] = request.form['email'] if 'email' in request.form else ''
        mail = re.compile('[!-~]+@[\w\-.]+\.[a-zA-Z]+')
        m = re.match(mail,postdata['email'])
        if not m:
            errors.append('正しいメールアドレスを入力してください。')
        if has_email(postdata['email']):
            errors.append('すでにこのメールアドレスで回答済みです。')
        postdata['age'] = request.form['age'] if 'age' in request.form else ''
        programs = request.form.getlist('program') if 'program' in request.form else ''
        postdata['program']['PHP'] = 'checked' if 'PHP' in programs else ''
        postdata['program']['JavaScript'] = 'checked' if 'JavaScript' in programs else ''
        postdata['program']['Python'] = 'checked' if 'Python' in programs else ''
        postdata['program']['Java'] = 'checked' if 'Java' in programs else ''
        postdata['program']['C/C++'] = 'checked' if 'C/C++' in programs else ''
        postdata['program']['C#'] = 'checked' if 'C#' in programs else ''
        postdata['program']['Ruby'] = 'checked' if 'Ruby' in programs else ''
        postdata['pc'] = request.form['pc'] if 'pc' in request.form else ''
        maker = request.form['maker'] if 'maker' in request.form else ''
        postdata['maker'] = ['selected' if m==maker else '' for m in makers]
        postdata['comments'] = request.form['comments'] if 'comments' in request.form else ''
        if not errors:
            sql = 'INSERT INTO answers (name,email,age,program,pc,maker,comments) VALUES (?,?,?,?,?,?,?)'
            if not maker:
                maker = 'その他'
            exec(sql,postdata['name'],postdata['email'],postdata['age'],'|'.join(programs),postdata['pc'],maker,postdata['comments'])
            return render_template('thanks.html', postdata=postdata, programs=programs, maker=maker)
    return render_template('index.html', postdata=postdata, errors=errors)

@app.route('/survey/admin/', methods=['GET', 'POST'])
def admin():
    if not 'username' in session:
        return redirect(url_for('login'))
    username = session['username']
    head = ['回答日時','名前','メールアドレス','年齢','興味のあるプログラミング言語','学習に使っているパソコン','パソコンメーカー','コメント']
    if request.method == 'POST':
        sql = 'SELECT * FROM answers'
        answers = exec(sql)
        if 'download' in request.form:
            with open(csv_path, 'w', newline='') as cf:
                csvout = csv.writer(cf)
                csvout.writerow(head)
                for answer in answers:
                    csvout.writerow(answer.values())
            return send_file('static/download.csv',mimetype='text/csv',download_name='downlaod.csv',as_attachment=True)
        if 'delete' in request.form:
            email = request.form['delete']
            sql = 'DELETE FROM answers WHERE email=?'
            exec(sql, email)
        if 'alldel' in request.form:
            sql = 'DELETE FROM answers'
            exec(sql)
    sql = 'SELECT * FROM answers'
    answers = exec(sql)
    return render_template('admin.html', answers=answers)

@app.route('/survey/admin/login', methods=['GET','POST'])
def login():
    if 'username' in session:
        return redirect(url_for('admin'))
    error = ''
    if request.method == 'POST':
        username = request.form['username']

        password = request.form['password']
        sql = 'SELECT * FROM siteadmin WHERE username=?'
        user = exec(sql, username)
        if not user or not check_password_hash(user[0]['password'], password):
            error = 'ログインに失敗しました。'
        else:
            session['username'] = username
            return redirect(url_for('admin'))

        #自身でハッシュ化する場合
        #password = to_hash(request.form['password'])
        #sql = 'SELECT * FROM siteadmin WHERE username=? AND password=?'
        #result = exec(sql, username, password)
        #if result:
        #    session['username'] = username
        #    return redirect(url_for('admin'))
        #else:
        #    error = 'ログイン失敗'
    return render_template('login.html', error=error)

@app.route('/survey/admin/logout')
def logout():
    if not 'username' in session:
        return redirect(url_for('login'))
    username = session['username']
    session.pop('username', None)
    return render_template('logout.html', username=username)

@app.route('/survey/admin/leave')
def leave():
    if not 'username' in session:
        return redirect(url_for('login'))
    username = session['username']
    session.pop('username', None)
    sql = 'DELETE FROM siteadmin WHERE username=?'
    exec(sql, username)
    return render_template('leave.html', username=username)

@app.route('/survey/admin/signup', methods=['GET','POST'])
def signup():
    if 'username' in session:
        return redirect(url_for('admin'))
    error = ''
    exist = ''
    sql = 'SELECT * FROM siteadmin'
    result = exec(sql)
    if result:
        exist = '管理者はすでに登録済みです。'
    else:
        if request.method == 'POST':
            username = request.form['username']
            pwd = re.search(re.compile('(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[\W_])[\w\W]{8,32}$'), request.form['password'])
            if pwd != None:
                #password = to_hash(request.form['password'])
                password = generate_password_hash(request.form['password'])
                sql = 'INSERT INTO siteadmin (username, password) VALUES (?, ?)'
                exec(sql, username, password)
                session['username'] = username
                return redirect(url_for('admin'))
            else:
                error = 'パスワードは8~32文字で大小文字英字数字記号をそれぞれ1文字以上含める必要があります。'
    return render_template('signup.html', error=error, exist=exist)

if __name__ == '__main__':
    app.run(port=8000, debug=True)
