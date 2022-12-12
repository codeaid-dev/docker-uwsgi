from flask import Flask, render_template
import datetime

app = Flask(__name__)

@app.route('/')
def index():
    now = datetime.datetime.now().strftime('%Y年%m月%d日%H:%M:%S.%f')
    return render_template('sample.html', page_name='トップページ！！', time=now)

@app.route('/sample')
def sample():
    now = datetime.datetime.now().strftime('%Y年%m月%d日%H:%M:%S')
    return render_template('sample.html', page_name='サンプルページ！！', time=now)