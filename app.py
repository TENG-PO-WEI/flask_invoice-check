from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

# 初始化 Flask 應用程式
app = Flask(__name__)

def get_winning_numbers():
    """
    從財政部電子發票整合服務平台爬取最新開獎號碼。
    此函數會嘗試從網站獲取資料，並以字典形式返回各獎項號碼。
    如果發生錯誤，則返回 None 和錯誤訊息。
    """
    url = 'https://invoice.etax.nat.gov.tw/index.html'
    try:
        web = requests.get(url, timeout=10)
        web.raise_for_status() # 檢查 HTTP 請求是否成功
        web.encoding = 'utf-8' # 設定編碼以正確處理中文

        soup = BeautifulSoup(web.text, 'html.parser')
        # 選擇包含獎號的 HTML 元素，這些元素有 'etw-tbiggest' 這個 CSS class
        # .container-fluid 是外層的容器，確保選擇範圍正確
        td = soup.select('.container-fluid')[0].select('.etw-tbiggest')

        # 擷取各獎項號碼並去除前後空白
        special_prize = td[0].getText().strip() # 特別獎 (1000 萬元)
        grand_prize = td[1].getText().strip() # 特獎 (200 萬元)

        # 頭獎有三組號碼，我們需要取其各自的最後八碼
        # 原始資料可能包含其他文字，例如「本期發票號碼：」
        first_prize_raw = [td[2].getText(), td[3].getText(), td[4].getText()]
        first_prize = [num_str.strip()[-8:] for num_str in first_prize_raw]

        # 成功時返回包含所有獎號的字典，以及 None 作為錯誤訊息
        return {
            "special_prize": special_prize,
            "grand_prize": grand_prize,
            "first_prize": first_prize
        }, None
    except requests.exceptions.RequestException as e:
        # 處理網路連線相關的錯誤
        return None, f'無法連接至電子發票網站，請檢查網路連線或稍後再試。詳細錯誤: {e}'
    except IndexError:
        # 處理無法找到預期 HTML 元素的錯誤，可能是網站結構改變
        return None, '無法解析發票號碼，網站結構可能已改變。'
    except Exception as e:
        # 處理其他未預期的錯誤
        return None, f'發生未知錯誤: {e}'

@app.route('/', methods=['GET'])
def get_prizes():
    """
    此端點提供最新統一發票開獎號碼的 JSON 資料。
    當您對根路徑 (/) 發送 GET 請求時，會返回這些號碼。
    """
    prizes, error_message = get_winning_numbers()
    if error_message:
        # 如果獲取開獎號碼時發生錯誤，返回錯誤訊息和 HTTP 500 狀態碼
        return jsonify({"status": "error", "message": error_message}), 500
    else:
        # 成功獲取號碼時，返回 JSON 格式的資料
        response_data = {
            "status": "success",
            "message": "最新統一發票開獎號碼",
            "prizes": prizes,
            "instructions": "若要兌獎，請向 /check 端點發送 POST 請求，並在 JSON 請求主體中包含 'invoice_number' 欄位 (例如: {'invoice_number': '12345678'})。"
        }
        return jsonify(response_data)

@app.route('/check', methods=['POST'])
def check_invoice():
    """
    此端點接收一個發票號碼，並返回兌獎結果。
    您需要向此端點發送一個 POST 請求，並在請求的 JSON 主體中包含 'invoice_number'。
    """
    # 嘗試從請求中獲取 JSON 資料
    data = request.get_json()
    # 檢查是否提供了 JSON 資料以及 'invoice_number' 欄位
    if not data or 'invoice_number' not in data:
        return jsonify({"status": "error", "message": "請在 JSON body 中提供 'invoice_number' 欄位。"}), 400

    # 取得使用者輸入的發票號碼並去除空白
    user_input_num = str(data['invoice_number']).strip()

    # 再次獲取最新開獎號碼以進行兌獎比對
    prizes, error_message = get_winning_numbers()

    if error_message:
        # 如果無法取得開獎號碼，則無法進行兌獎
        return jsonify({"status": "error", "message": f"無法取得最新開獎號碼進行兌獎: {error_message}"}), 500

    # 從獲取的獎號字典中取出各獎項號碼
    special_prize = prizes["special_prize"]
    grand_prize = prizes["grand_prize"]
    first_prize = prizes["first_prize"]

    # 初始化預設結果訊息
    result_message = "很抱歉，沒中獎。"

    # 進行兌獎邏輯判斷
    # 先判斷特別獎和特獎，因為它們是最高獎項
    if user_input_num == special_prize:
        result_message = '恭喜中獎 **1000 萬元**！'
    elif user_input_num == grand_prize:
        result_message = '恭喜中獎 **200 萬元**！'
    else:
        matched = False
        # 檢查頭獎及後續的對獎規則（末七碼、末六碼、...、末三碼）
        for i in first_prize:
            if user_input_num == i:
                result_message = '恭喜中獎 **20 萬元**！'
                matched = True
                break
            elif user_input_num[-7:] == i[-7:]:
                result_message = '恭喜中獎 **4 萬元**！'
                matched = True
                break
            elif user_input_num[-6:] == i[-6:]:
                result_message = '恭喜中獎 **1 萬元**！'
                matched = True
                break
            elif user_input_num[-5:] == i[-5:]:
                result_message = '恭喜中獎 **4000 元**！'
                matched = True
                break
            elif user_input_num[-4:] == i[-4:]:
                result_message = '恭喜中獎 **1000 元**！'
                matched = True
                break
            elif user_input_num[-3:] == i[-3:]:
                result_message = '恭喜中獎 **200 元**！'
                matched = True
                break
        # 如果所有比對都未成功，則表示沒中獎
        if not matched:
            result_message = '很抱歉，**沒中獎**。'

    # 返回 JSON 格式的兌獎結果
    return jsonify({"status": "success", "invoice_number": user_input_num, "result": result_message})

if __name__ == '__main__':
    # 啟動 Flask 伺服器，debug=True 可以在開發時提供更詳細的錯誤訊息和自動重載功能
    app.run(debug=True)