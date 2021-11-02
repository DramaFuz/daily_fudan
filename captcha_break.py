import base64
import requests
import json
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')

def base64_api(uname, pwd, img, typeid):
    base64_data = base64.b64encode(img)
    b64 = base64_data.decode()
    data = {"username": uname, "password": pwd, "typeid": typeid, "image": b64}
    result = json.loads(requests.post("http://api.ttshitu.com/predict", json=data).text)
    return result

def getCaptchaData(zlapp):
    url = 'https://zlapp.fudan.edu.cn/backend/default/code'
    headers = {'accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    'accept-encoding': 'gzip',
    'accept-language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
    'dnt': '1',
    'referer': 'https://zlapp.fudan.edu.cn/site/ncov/fudanDaily',
    'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
    'sec-ch-ua-mobile': '?0',
    'sec-fetch-dest': 'image',
    'sec-fetch-mode': 'no-cors',
    'sec-fetch-site': 'same-origin',
    "User-Agent": zlapp.UA}
    res = zlapp.session.get(url, headers=headers)
    return res.content

class DailyFDCaptcha:
    zlapp = None
    uname = ''
    pwd = ''
    typeid = 2 # 纯英文

    def __init__(self, uname, pwd, zlapp):
        self.zlapp = zlapp
        self.uname = uname
        self.pwd = pwd

    def __call__(self):
        img = getCaptchaData(self.zlapp)
        result = base64_api(self.uname, self.pwd, img, self.typeid)
        if result['success']:
            logging.info("Sucessfully get Captcha Result.")
            return result["data"]["result"]
        else:
            logging.info("Error get Captcha Result.")
            return None
