from flask import Flask, render_template
import datetime
import mysql.connector
from mysql.connector import errorcode
import logging
from contextlib import closing
app = Flask(__name__)

debug_handler = logging.FileHandler('debug.log')
debug_handler.setLevel(logging.DEBUG)
app.logger.addHandler(debug_handler)
error_handler = logging.FileHandler('error.log')
error_handler.setLevel(logging.ERROR)
app.logger.addHandler(error_handler)
app.logger.setLevel(logging.DEBUG)

@app.route('/')
def index():
    now = datetime.datetime.now().strftime('%Y年%m月%d日%H:%M:%S.%f')
    return render_template('sample.html', page_name='トップページ！！', time=now)

@app.route('/mysqlsample')
def sample():
    now = datetime.datetime.now().strftime('%Y年%m月%d日%H:%M:%S')
    try:
        res = ''
        with closing(mysql.connector.connect(user='root', password='password',
                                host='mysql', database='sampledb')) as cnx:
            cur = cnx.cursor(prepared=True)
            res += '接続成功<br>'
            cur.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY,
                        name VARCHAR(20),
                        score INTEGER)''')
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
            cnx.commit()

    except mysql.connector.Error as err:
        app.logger.error(err)

    return render_template('mysqlsample.html', page_name='MySQLサンプルページ！！', time=now, result=res)

if __name__ == '__main__':
    app.run(port=8000, debug=True)