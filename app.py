from flask import Flask, request, render_template_string
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route('/')
def home():
    return '<a href="/invoice">點我兌獎</a>'

@app.route('/invoice', methods=['GET', 'POST'])
def invoice():
    result = ""
    if request.method == 'POST':
        try:
            num = request.form['num'].strip()
            url = 'https://invoice.etax.nat.gov.tw/index.html'
            web = requests.get(url, timeout=10)
            web.raise_for_status()
            web.encoding = 'utf-8'

            soup = BeautifulSoup(web.text, 'html.parser')
            td = soup.select('.container-fluid')[0].select('.etw-tbiggest')
            ns = td[0].getText()
            n1 = td[1].getText()
            n2 = [td[2].getText()[-8:], td[3].getText()[-8:], td[4].getText()[-8:]]  # 頭獎

            if num == ns:
                result = "🎉 恭喜中獎 1000 萬元"
            elif num == n1:
                result = "🎉 恭喜中獎 200 萬元"
            else:
                matched = False
                for i in n2:
                    if num == i:
                        result = "🎉 恭喜中獎 20 萬元"
                        matched = True
                        break
                    elif num[-7:] == i[-7:]:
                        result = "🎉 恭喜中獎 4 萬元"
                        matched = True
                        break
                    elif num[-6:] == i[-6:]:
                        result = "🎉 恭喜中獎 1 萬元"
                        matched = True
                        break
                    elif num[-5:] == i[-5:]:
                        result = "🎉 恭喜中獎 4000 元"
                        matched = True
                        break
                    elif num[-4:] == i[-4:]:
                        result = "🎉 恭喜中獎 1000 元"
                        matched = True
                        break
                    elif num[-3:] == i[-3:]:
                        result = "🎉 恭喜中獎 200 元"
                        matched = True
                        break
                if not matched:
                    result = "😢 很抱歉，沒中獎"
        except Exception as e:
            result = f"錯誤發生：{e}"

    return render_template_string('''
        <h2>電子發票兌獎系統</h2>
        <form method="post">
            發票號碼：<input type="text" name="num">
            <input type="submit" value="兌獎">
        </form>
        <p>{{ result }}</p>
        <a href="/">回首頁</a>
    ''', result=result)

if __name__ == '__main__':
    app.run(debug=True)
