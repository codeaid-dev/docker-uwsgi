import mysql.connector
from mysql.connector import errorcode

try:
    cnx = mysql.connector.connect(user='root', password='password',
                                host='mysql', database='sampledb')
    cur = cnx.cursor(prepared=True)
    print('接続成功')
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name VARCHAR(20),
                score INTEGER);''')
    print('テーブル作成')

    data = [(1, 'Yamada', 85),(2, 'Tanaka', 79),(3, 'Suzuki', 63)]
    for d in data:
        cur.execute("INSERT INTO users VALUES(?, ?, ?);", d)
    #cur.execute("INSERT INTO users VALUES(1, 'Yamada', 85);")
    #cur.execute("INSERT INTO users VALUES(2, 'Tanaka', 79);")
    #cur.execute("INSERT INTO users VALUES(3, 'Suzuki', 63);")
    print('データ挿入')

    cur.execute("SELECT * FROM users WHERE score >= ?;", (70,))
    #cur.execute("SELECT * FROM users WHERE score >= 70;")
    result = cur.fetchall()
    print('70点以上選択')
    for id,name,score in result:
        print(f'{id}\t{name}\t{score}')

    cur.execute("DROP TABLE users;")
    print('テーブル削除')
    cnx.commit()

except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("ユーザー名かパスワードが間違っています")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("データーベースがありません")
    elif err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
        print("そのテーブルはすでに存在しています")
    else:
        print(err)

finally:
    if cnx:
        cnx.close()
