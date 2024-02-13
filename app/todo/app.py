from flask import Flask, render_template, request, redirect, url_for, session
import os, sqlite3, hashlib, re, logging
from datetime import timedelta
from contextlib import closing
from werkzeug.security import check_password_hash, generate_password_hash
import mysql.connector
import random, string

app = Flask(__name__)
app.secret_key = ''.join(random.choices(string.ascii_letters + string.digits, k=16)) #セッション情報を暗号化するためのキー
app.permanent_session_lifetime = timedelta(seconds=60) #セッション有効期限60秒
base_path = os.path.dirname(__file__)
db_path = base_path + '/todo.db'

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
                                host='mysql', database='todo')) as con: #MySQL
        #with closing(sqlite3.connect(db_path)) as con: #SQLite
            cur = con.cursor(prepared=True,dictionary=True) #MySQL
            #cur = con.cursor() #SQLite
            #For SQLite using AUTOINCREMENT, for MySQL using AUTO_INCREMENT
            cur.execute('''CREATE TABLE IF NOT EXISTS users (
                username VARCHAR(256) NOT NULL PRIMARY KEY,
                password VARCHAR(256) NOT NULL
                )''')
            cur.execute('''CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,
                username VARCHAR(256) NOT NULL,
                task VARCHAR(256) NOT NULL
                )''')
    except mysql.connector.Error as e: #MySQL
    #except sqlite3.Error as e: #SQLite
        app.logger.error(e)
create_db()

def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

def exec(sql, *arg):
    try:
        with closing(mysql.connector.connect(user='root', password='password',
                                host='mysql', database='todo')) as con: #MySQL
        #with closing(sqlite3.connect(db_path)) as con: #SQLite
            con.row_factory = dict_factory
            cur = con.cursor(prepared=True,dictionary=True) #MySQL
            #cur = con.cursor() #SQLite
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
    salt = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    password += salt
    text = password.encode('utf-8')
    hash = hashlib.sha256(text).hexdigest()
    return salt + hash

def verify_password(password, hash):
    salt, digest = hash[:16], hash[16:]
    password += salt
    text = password.encode('utf-8')
    hash = hashlib.sha256(text).hexdigest()
    return digest == hash

@app.route('/todo/', methods=['GET', 'POST'])
def index():
    if not 'username' in session:
        return redirect(url_for('login'))
    username = session['username']
    sql = 'SELECT * FROM tasks WHERE username=?'
    tasks = exec(sql, username)
    if request.method == 'POST':
        if 'add' in request.form:
            sql = 'INSERT INTO tasks (username, task) VALUES (?, ?)'
            exec(sql, username, request.form['task'])
            return redirect(url_for('index'))
    if request.method == 'GET':
        id = request.args.get('del')
        if id:
            sql = 'DELETE FROM tasks WHERE id=? AND username=?'
            exec(sql, id, username)
            return redirect(url_for('index'))
    return render_template('index.html', username=username, tasks=tasks, id=id)

@app.route('/todo/login', methods=['GET','POST'])
def login():
    if 'username' in session:
        return redirect(url_for('index'))
    error = ''
    if request.method == 'POST':
        username = request.form['username']

        password = request.form['password']
        sql = 'SELECT * FROM users WHERE username=?'
        user = exec(sql, username)
        if not user:
            error = 'ユーザー名が誤っています。'
        elif not check_password_hash(user[0]['password'], password):
        #elif not verify_password(password, user[0]['password']):
            error = 'パスワードが誤っています。'
        else:
            session['username'] = username
            return redirect(url_for('index'))

    return render_template('login.html', error=error)

@app.route('/todo/logout')
def logout():
    if not 'username' in session:
        return redirect(url_for('login'))
    username = session['username']
    session.pop('username', None)
    return render_template('logout.html', username=username)

@app.route('/todo/leave')
def leave():
    if not 'username' in session:
        return redirect(url_for('login'))
    username = session['username']
    session.pop('username', None)
    sql = 'DELETE FROM users WHERE username=?'
    exec(sql, username)
    sql = 'DELETE FROM tasks WHERE username=?'
    exec(sql, username)
    return render_template('leave.html', username=username)

@app.route('/todo/signup', methods=['GET','POST'])
def signup():
    if 'username' in session:
        return redirect(url_for('index'))
    error = ''
    if request.method == 'POST':
        username = request.form['username']
        pwd = re.search(re.compile('(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[\W_])[\w\W]{8,32}$'), request.form['password'])
        if pwd != None:
          print('有効なパスワードです')
          password = generate_password_hash(request.form['password'])
          #password = to_hash(request.form['password'])
          sql = 'SELECT * FROM users WHERE username=?'
          result = exec(sql, username)
          if result:
              error = 'このユーザー名は登録できません。'
          else:
              sql = 'INSERT INTO users (username, password) VALUES (?, ?)'
              exec(sql, username, password)
              session['username'] = username
              return redirect(url_for('index'))
        else:
            error = 'パスワードは8~32文字で大小文字英字数字記号をそれぞれ1文字以上含める必要があります。'
    return render_template('signup.html', error=error)

@app.route('/todo/edit', methods=['GET','POST'])
def edit():
    if not 'username' in session:
        return redirect(url_for('login'))
    username = session['username']
    if request.method == 'POST':
        if 'edit' in request.form:
            task = request.form['task']
            id = request.form['id']
            sql = 'UPDATE tasks SET task=? WHERE username=? AND id=?'
            exec(sql, task, username, id)
            return redirect(url_for('index'))
    if request.method == 'GET':
        id = request.args.get('edit')
        if id:
            sql = 'SELECT * FROM tasks WHERE id=? AND username=?'
            task = exec(sql, id, username)[0]
    return render_template('edit.html', username=username, id=id, task=task)

if __name__ == '__main__':
    app.run(debug=True)
