from flask import Flask, request, render_template_string
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def invoice():
    # 初始化結果訊息
    result = ""

    # 檢查是否為 POST 請求 (使用者提交表單)
    if request.method == 'POST':
        try:
            # 取得使用者輸入的發票號碼並移除前後空白
            num = request.form['num'].strip()

            # 驗證輸入：檢查是否為8位數字
            if not num.isdigit() or len(num) != 8:
                result = "請輸入8位數字"
            else:
                # 定義財政部統一發票中獎號碼查詢網址
                url = 'https://invoice.etax.nat.gov.tw/index.html'
                # 發送 HTTP GET 請求獲取網頁內容，設定超時時間為10秒
                web = requests.get(url, timeout=10)
                # 檢查請求是否成功，若不成功則拋出異常
                web.raise_for_status()
                # 設定網頁編碼為 UTF-8
                web.encoding = 'utf-8'

                # 使用 BeautifulSoup 解析網頁內容
                soup = BeautifulSoup(web.text, 'html.parser')
                # 選擇包含中獎號碼的特定 HTML 元素
                td = soup.select('.container-fluid')[0].select('.etw-tbiggest')

                # 提取各獎項號碼並移除空白
                ns = td[0].getText().strip()  # 特別獎號碼
                n1 = td[1].getText().strip()  # 特獎號碼
                # 頭獎號碼可能有多組，取每組的最後8位數字
                n2 = [td[2].getText().strip()[-8:], td[3].getText().strip()[-8:], td[4].getText().strip()[-8:]] # 頭獎號碼

                # 進行發票號碼比對
                if num == ns:
                    result = "🎉 恭喜中獎 1000 萬元"
                elif num == n1:
                    result = "� 恭喜中獎 200 萬元"
                else:
                    matched = False # 標記是否中獎
                    for i in n2:
                        if num == i: # 完全符合頭獎號碼
                            result = "🎉 恭喜中獎 20 萬元"
                            matched = True
                            break # 中獎後跳出迴圈
                        elif num[-7:] == i[-7:]: # 符合末7碼
                            result = "🎉 恭喜中獎 4 萬元"
                            matched = True
                            break
                        elif num[-6:] == i[-6:]: # 符合末6碼
                            result = "🎉 恭喜中獎 1 萬元"
                            matched = True
                            break
                        elif num[-5:] == i[-5:]: # 符合末5碼
                            result = "🎉 恭喜中獎 4000 元"
                            matched = True
                            break
                        elif num[-4:] == i[-4:]: # 符合末4碼
                            result = "🎉 恭喜中獎 1000 元"
                            matched = True
                            break
                        elif num[-3:] == i[-3:]: # 符合末3碼 (普獎)
                            result = "🎉 恭喜中獎 200 元"
                            matched = True
                            break
                    # 如果所有獎項都沒中
                    if not matched:
                        result = "😢 很抱歉，沒中獎"
        except requests.exceptions.RequestException as req_err:
            # 捕獲網路請求相關的錯誤
            result = f"網路請求錯誤：{req_err}，請檢查網路連線或稍後再試。"
        except Exception as e:
            # 捕獲其他可能發生的通用錯誤
            result = f"發生錯誤：{e}"

    # 返回渲染後的 HTML 字串。此處為簡化的範例，實際應用中應將 HTML 放在獨立的模板檔案中。
    # 這裡的 HTML 僅包含必要的表單和結果顯示，不包含完整的網頁結構和樣式。
    return render_template_string('''
        <h2>統一發票兌獎系統</h2>
        <form method="post">
            發票號碼：<input type="text" name="num" placeholder="請輸入8位數字" maxlength="8" pattern="[0-9]{8}" title="請輸入8位數字">
            <input type="submit" value="兌獎">
        </form>
        <p>{{ result }}</p>
        <a href="https://invoice.etax.nat.gov.tw/index.html" target="_blank" rel="noopener noreferrer">財政部統一發票中獎號碼</a>
    ''', result=result)

if __name__ == '__main__':
    # 在偵錯模式下運行 Flask 應用程式
    app.run(debug=True)
