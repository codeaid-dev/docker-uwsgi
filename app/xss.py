from flask import Flask, request
from markupsafe import escape

app = Flask(__name__)

@app.route('/xss',methods=['GET','POST'])
def xss():
    name = ''
    if 'name' in request.form:
        name = request.form['name']
    if name:
        return f'''
            <html lang="ja">
                <head>
                <title>クロスサイト・スクリプティング対策</title>
                </head>
                <body>
                <p>「{escape(name)}」さん、こんにちは！</p>
                <a href="/xss">戻る</a>
                </body>
            </html>'''
    else:
        return '''
            <html lang="ja">
                <head>
                <title>クロスサイト・スクリプティング対策</title>
                </head>
                <body>
                <form method="POST">
                <p>名前：<input type="test" name="name"></p>
                <button type="submit">表示</button>
                </body>
            </html>'''

if __name__ == '__main__':
    app.run(debug=True)