from flask import Flask, render_template
import datetime
import sqlite3
from contextlib import closing
dbname = './db/sample.db'
app = Flask(__name__)

@app.route('/')
def index():
    now = datetime.datetime.now().strftime('%Y年%m月%d日%H:%M:%S.%f')
    return render_template('sample.html', page_name='トップページ！！', time=now)

@app.route('/sqlitesample')
def sample():
    now = datetime.datetime.now().strftime('%Y年%m月%d日%H:%M:%S')
    res = ''
    try:
        with closing(sqlite3.connect('./db/sample.db')) as con:
            res += '接続成功<br>'
            cur = con.cursor()
            cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT,
                score INTEGER
            )''')
            res += 'テーブル作成<br>'

            cur.execute("INSERT INTO users VALUES(1, 'Yamada', 85)")
            cur.execute("INSERT INTO users VALUES(2, 'Tanaka', 79)")
            cur.execute("INSERT INTO users VALUES(3, 'Suzuki', 63)")
            res += 'データ挿入<br>'

            cur.execute("SELECT * FROM users WHERE score >= 70")
            result = cur.fetchall()
            res += '70点以上選択<br>'
            for id,name,score in result:
                res += f'{id}\t{name}\t{score}<br>'

            cur.execute("DROP TABLE users")
            res += 'テーブル削除<br>'
            con.commit()
    except sqlite3.Error as e:
        app.logger.error(e)

    return render_template('sqlitesample.html', page_name='SQLiteサンプルページ！！', time=now, result=res)

if __name__ == '__main__':
    app.run(port=8000, debug=True)