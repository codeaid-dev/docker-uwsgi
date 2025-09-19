from flask import Flask, render_template, request, redirect, url_for, session, abort
import os, sqlite3, hashlib, re
from datetime import timedelta
from contextlib import closing
from werkzeug.security import check_password_hash, generate_password_hash
import mysql.connector
from base64 import b64encode, b64decode

app = Flask(__name__)
app.secret_key = b64encode(os.urandom(16)).decode() #セッション情報を暗号化するためのキー
app.permanent_session_lifetime = timedelta(minutes=10) #セッション有効期限10分
base_path = os.path.dirname(__file__)
db_path = base_path + '/static/blog.db'

def create_db():
    try:
        with closing(mysql.connector.connect(user='root', password='password',
                                host='mysql', database='blog')) as con: #MySQL
        #with closing(sqlite3.connect(db_path)) as con: #SQLite
            cur = con.cursor(prepared=True,dictionary=True) #MySQL
            #cur = con.cursor() #SQLite
            #For SQLite using AUTOINCREMENT, for MySQL using AUTO_INCREMENT
            cur.execute('''CREATE TABLE IF NOT EXISTS siteadmin (
                username VARCHAR(256) NOT NULL PRIMARY KEY,
                password VARCHAR(256) NOT NULL
                )''')
            #MySQL
            cur.execute('''CREATE TABLE IF NOT EXISTS posts (
                id INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                title VARCHAR(256) NOT NULL,
                article VARCHAR(256) NOT NULL
                )''')
            #SQLite
            #cur.execute('''CREATE TABLE IF NOT EXISTS posts (
            #    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            #   created_at DATETIME DEFAULT (DATETIME('now','localtime')),
            #    updated_at DATETIME DEFAULT (DATETIME('now','localtime')),
            #    title VARCHAR(256) NOT NULL,
            #    article VARCHAR(256) NOT NULL
            #    )''')
            #cur.execute('''CREATE TRIGGER IF NOT EXISTS trigger_updated_at AFTER UPDATE ON posts
            #    BEGIN
            #        UPDATE posts SET updated_at = DATETIME('now', 'localtime') WHERE rowid == NEW.rowid;
            #    END''')
    except mysql.connector.Error as e: #MySQL
    #except sqlite3.Error as e: #SQLite
        app.logger.error(e)
create_db()

def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

def exec(sql, *arg):
    res = None
    try:
        with closing(mysql.connector.connect(user='root', password='password',
                                host='mysql', database='blog')) as con: #MySQL
        #with closing(sqlite3.connect(db_path)) as con: #SQLite
            con.row_factory = dict_factory
            cur = con.cursor(prepared=True,dictionary=True) #MySQL
            #cur = con.cursor() #SQLite
            if not arg:
                cur.execute(sql)
            else:
                cur.execute(sql, arg)
            if sql.lstrip().upper().startswith('SELECT'):
                res = cur.fetchall()
            con.commit()
    except mysql.connector.Error as e: #MySQL
    #except sqlite3.Error as e: #SQLite
        app.logger.error(e)
    return res

def hash_password(password):
    salt = os.urandom(16) #16バイトのバイト列
    digest = hashlib.pbkdf2_hmac('sha256',password.encode('utf-8'),salt,10000)
    return b64encode(salt + digest).decode()

def verify_password(password, hash):
    b = b64decode(hash)
    salt, verify = b[:16], b[16:]
    digest = hashlib.pbkdf2_hmac('sha256',password.encode('utf-8'),salt,10000)
    return digest == verify

@app.route('/')
def index():
    sql = 'SELECT * FROM posts ORDER BY updated_at DESC'
    posts = exec(sql)
    post_id = request.args.get('post')
    if post_id is None or post_id=='':
        if posts:
            for post in posts:
                #index = post['created_at'].find(' ') #SQLite
                #post['created_at'] = post['created_at'][:index].replace('-','/') #SQLite
                post['created_at'] = post['created_at'].strftime('%Y/%m/%d') #MySQL
                #index = post['updated_at'].find(' ') #SQLite
                #post['updated_at'] = post['updated_at'][:index].replace('-','/') #SQLite
                post['updated_at'] = post['updated_at'].strftime('%Y/%m/%d') #MySQL

        return render_template('index.html', posts=posts)
    else:
        for post in posts:
            if post['id'] == int(post_id):
                return render_template('post.html', post=post)
        else:
            abort(404)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/admin/')
def admin():
    if not 'username' in session:
        return redirect(url_for('login'))
    username = session['username']

    sql = 'SELECT * FROM posts ORDER BY updated_at DESC'
    posts = exec(sql)
    if posts:
        for post in posts:
            #index = post['created_at'].find(' ') #SQLite
            #post['created_at'] = post['created_at'][:index].replace('-','/') #SQLite
            post['created_at'] = post['created_at'].strftime('%Y/%m/%d') #MySQL
            #index = post['updated_at'].find(' ') #SQLite
            #post['updated_at'] = post['updated_at'][:index].replace('-','/') #SQLite
            post['updated_at'] = post['updated_at'].strftime('%Y/%m/%d') #MySQL

    return render_template('admin.html', posts=posts)

@app.route('/admin/add', methods=['GET','POST'])
def add():
    if not 'username' in session:
        return redirect(url_for('login'))
    username = session['username']
    if request.method == 'POST':
        title = request.form['title']
        article = request.form['article']
        sql = 'INSERT INTO posts (title, article) VALUES (?, ?)'
        exec(sql, title, article)
        return redirect(url_for('admin'))

    return render_template('add.html')

@app.route('/admin/edit', methods=['GET','POST'])
def edit():
    if not 'username' in session:
        return redirect(url_for('login'))
    username = session['username']
    post_id = request.args.get('id')
    if post_id:
        sql = 'SELECT * FROM posts WHERE id=?'
        post = exec(sql, post_id)
        if post:
            post = post[0]
            return render_template('edit.html', post=post)
        else:
            abort(404)
    if request.method == 'POST':
        if 'update' in request.form:
            sql = 'UPDATE posts SET title=?, article=? WHERE id=?'
            exec(sql, request.form['title'], request.form['article'], request.form['id'])
        elif 'delete' in request.form:
            sql = 'DELETE FROM posts WHERE id=?'
            exec(sql, request.form['id'])
        return redirect(url_for('admin'))

@app.route('/admin/login', methods=['GET','POST'])
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
        #if not user or not verify_password(password, user[0]['password']):
            error = 'ログインに失敗しました。'
        else:
            session['username'] = username
            return redirect(url_for('admin'))

    return render_template('login.html', error=error)

@app.route('/admin/logout')
def logout():
    if not 'username' in session:
        return redirect(url_for('login'))
    username = session['username']
    session.pop('username', None)
    return render_template('logout.html', username=username)

@app.route('/admin/leave')
def leave():
    if not 'username' in session:
        return redirect(url_for('login'))
    username = session['username']
    session.pop('username', None)
    sql = 'DELETE FROM siteadmin WHERE username=?'
    exec(sql, username)
    return render_template('leave.html', username=username)

@app.route('/admin/signup', methods=['GET','POST'])
def signup():
    if 'username' in session:
        return redirect(url_for('admin'))
    error = ''
    exist = ''
    sql = 'SELECT * FROM siteadmin'
    result = exec(sql)
    if result:
        exist = '管理者はすでに登録済みです。'
    if request.method == 'POST':
        username = request.form['username']
        pwd = re.search(re.compile('(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[\W_])[\w\W]{8,32}$'), request.form['password'])
        if pwd != None:
            password = generate_password_hash(request.form['password'])
            #password = hash_password(request.form['password'])
            sql = 'INSERT INTO siteadmin (username, password) VALUES (?, ?)'
            exec(sql, username, password)
            session['username'] = username
            return redirect(url_for('admin'))
        else:
            error = 'パスワードは8~32文字で大小文字英字数字記号をそれぞれ1文字以上含める必要があります。'
    return render_template('signup.html', error=error, exist=exist)

if __name__ == '__main__':
    app.run(port=8000, debug=True)
