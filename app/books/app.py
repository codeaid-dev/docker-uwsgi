from flask import Flask, render_template, request, redirect, url_for
import os, sqlite3, logging
from contextlib import closing

TITLE = '書籍データ庫'
app = Flask(__name__)
base_path = os.path.dirname(__file__)
db_path = base_path + '/books.db'

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
            cur.execute('''CREATE TABLE IF NOT EXISTS books (
                isbn VARCHAR(17) NOT NULL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                price INTEGER NOT NULL,
                page INTEGER NOT NULL,
                date TEXT NOT NULL)''')
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

def check_isbn(isbn):
    res = exec('SELECT * FROM books WHERE isbn=?', isbn)
    if len(res) > 0:
        return False
    return True

@app.route('/')
def index():
    create_db()
    return render_template('index.html', title=TITLE)

@app.route('/update', methods=['POST'])
def update():
    error = []
    normal = ''
    values = {'isbn':'','name':'','price':'','page':'','date':''}
    if 'update' in request.form: # 閲覧ページから修正ボタンが押された
        values['isbn'] = request.form['update']
    else:
        values['isbn'] = request.form['isbn']
    values['name'] = request.form['name']
    values['price'] = request.form['price']
    if not request.form['price'].isdigit():
        error.append('価格は数字を入力してください。')
    values['page'] = request.form['page']
    if not request.form['page'].isdigit():
        error.append('ページ数は数字を入力してください。')
    values['date'] = request.form['date']
    if not error:
        if not 'update' in request.form:
            exec('UPDATE books SET name=?, price=?, page=?, date=? WHERE isbn=?', request.form['name'], request.form['price'], request.form['page'], request.form['date'], request.form['isbn'])
            normal = '修正できました。'
    return render_template('update.html', title=TITLE, error=error, values=values, normal=normal)

@app.route('/read', methods=['GET','POST'])
def read():
    result = None
    delete = None
    if request.method == 'POST':
        if 'keyword' in request.form:
            name = "%"+request.form['keyword']+"%"
            result = exec('SELECT * FROM books WHERE isbn=? OR name LIKE ?', request.form['keyword'], name)
        if 'delete' in request.form: # 削除ボタンが押された
            exec('DELETE FROM books WHERE isbn=?', request.form['delete'])
            delete = request.form['delete']
    return render_template('read.html', title=TITLE, result=result, delete=delete)

@app.route('/write', methods=['GET','POST'])
def write():
    error = []
    normal = ''
    values = {'isbn':'','name':'','price':'','page':'','date':''}
    if request.method == 'POST':
        if 'isbn' in request.form:
            values['isbn'] = request.form['isbn']
            if not request.form['isbn'].isdigit():
                error.append('ISBNは数字で入力してください。')
        if 'name' in request.form:
            values['name'] = request.form['name']
        if 'price' in request.form:
            values['price'] = request.form['price']
            if not request.form['price'].isdigit():
                error.append('価格は数字を入力してください。')
        if 'page' in request.form:
            values['page'] = request.form['page']
            if not request.form['page'].isdigit():
                error.append('ページ数は数字を入力してください。')
        if 'date' in request.form:
            values['date'] = request.form['date']
        if not error:
            if check_isbn(values['isbn']):
                exec('INSERT INTO books (isbn, name, price, page, date) VALUES (?,?,?,?,?)',
                    values['isbn'], values['name'], values['price'], values['page'], values['date'])
                normal = '保存できました。'
            else:
                normal = '入力したISBNはすでに保存されています。'
        return render_template('write.html', title=TITLE, error=error, values=values, normal=normal)
    else:
        return render_template('write.html', title=TITLE, values=values)

if __name__ == '__main__':
    app.run(port=8000, debug=True)
