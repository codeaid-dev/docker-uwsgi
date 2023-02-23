import sqlite3
from contextlib import closing
try:
    with closing(sqlite3.connect('./db/sample.db')) as con:
        print('接続成功')

        cur = con.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        score INTEGER
                    )''')
        print('テーブル作成')

        data = [(1, 'Yamada', 85),(2, 'Tanaka', 79)]
        cur.executemany("INSERT INTO users VALUES(?, ?, ?)", data)
        cur.execute("INSERT INTO users VALUES(:id, :name, :score)", {'id':3,'name':'Suzuki','score':63})
        #cur.execute("INSERT INTO users VALUES(1, 'Yamada', 85)")
        #cur.execute("INSERT INTO users VALUES(2, 'Tanaka', 79)")
        #cur.execute("INSERT INTO users VALUES(3, 'Suzuki', 63)")
        print('データ挿入')

        cur.execute("SELECT * FROM users WHERE score >= ?", (70,))
        #cur.execute("SELECT * FROM users WHERE score >= 70")
        result = cur.fetchall()
        print('70点以上選択')
        for id,name,score in result:
            print(f'{id}\t{name}\t{score}')

        cur.execute("DROP TABLE users")
        print('テーブル削除')
        con.commit()
except sqlite3.Error as e:
    print(e)