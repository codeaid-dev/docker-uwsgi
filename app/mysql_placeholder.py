import mysql.connector
from mysql.connector import errorcode
from contextlib import closing
try:
    with closing(mysql.connector.connect(user='root', password='password',
                                host='mysql', database='sampledb')) as cnx:
        cur = cnx.cursor(prepared=True)
        print('接続成功')
        cur.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(20),
                    score INTEGER)''')
        print('テーブル作成')

        data = [(1, 'Yamada', 85),(2, 'Tanaka', 79),(3, 'Suzuki', 63)]
        for d in data:
            cur.execute("INSERT INTO users VALUES(?, ?, ?)", d)
        print('データ挿入')

        cur.execute("SELECT * FROM users WHERE score >= ?", (70,))
        result = cur.fetchall()
        print('70点以上選択')
        for id,name,score in result:
            print(f'{id}\t{name}\t{score}')

        cur.execute("DROP TABLE users")
        print('テーブル削除')
        cnx.commit()
except mysql.connector.Error as err:
    print(err)